import unittest

import numpy as np

from dictionaries import DIVIDER_RULES
from methods.switching import switching


class SwitchingTest(unittest.TestCase):
    def test_switching_completes_with_all_divisor_rules(self):
        cases = [
            ([[1000, 10, 1], [900, 9, 1]], [5, 5], [4, 3, 3],
             [[1, 0, 0], [1, 0, 0]]),
            ([[10, 0], [100, 0]], [1, 2], [2, 1], [[0, 0], [1, 0]]),
            ([[1, 1], [1, 1]], [3, 3], [3, 3], [[0, 0], [0, 0]]),
        ]
        for name, rule in DIVIDER_RULES.items():
            for votes, rows, targets, prior in cases:
                with self.subTest(rule=name, votes=votes):
                    allocation, demo = switching(votes, rows, targets, prior, rule)
                    np.testing.assert_array_equal(allocation.sum(axis=1), rows)
                    np.testing.assert_array_equal(allocation.sum(axis=0), targets)
                    self.assertTrue((allocation >= prior).all())
                    excess = sum(max(0, party['actual'] - party['goal'])
                                 for party in demo['data']['initial_allocation'])
                    self.assertEqual(len(demo['data']['switches']), excess)

    def test_switching_leaves_room_for_national_seats(self):
        allocation, _ = switching(
            [[100, 1], [100, 1]], [3, 3], [2, 6], [[0, 0], [0, 0]],
            DIVIDER_RULES['sainte-lague'])
        np.testing.assert_array_equal(allocation.sum(axis=1), [3, 3])
        np.testing.assert_array_equal(allocation.sum(axis=0), [2, 4])

    def test_provisional_allocation_can_exceed_party_target_before_switching(self):
        allocation, demo = switching(
            [[100, 80]], [3], [1, 2], [[1, 0]],
            DIVIDER_RULES['dhondt'])

        initial = demo['data']['initial_allocation']
        self.assertEqual([party['actual'] for party in initial], [2, 1])
        self.assertEqual(len(demo['data']['switches']), 1)
        np.testing.assert_array_equal(allocation, [[1, 2]])

    def test_flexible_switching_uses_the_best_cross_constituency_ratio(self):
        prior = np.array([[1, 0], [0, 1]])
        allocation, demo = switching(
            [[100, 80], [120, 1]], [1, 2], [2, 3], prior,
            DIVIDER_RULES['dhondt'],
            num_adjustment_seats=3,
            min_adj_seats=[0, 1],
            max_adj_seats=[2, 2],
        )

        np.testing.assert_array_equal(allocation.sum(axis=0), [2, 3])
        np.testing.assert_array_equal(
            allocation.sum(axis=1) - prior.sum(axis=1), [2, 1])
        switch = demo['data']['switches'][0]
        self.assertEqual(
            (switch['from_constituency'], switch['to_constituency']), (1, 0))
        self.assertAlmostEqual(switch['ratio'], 1.5)

    def test_flexible_switching_dense_positive_cases_finish_within_bounds(self):
        rng = np.random.default_rng(92)
        for rule in (DIVIDER_RULES['dhondt'],
                     DIVIDER_RULES['sainte-lague']):
            for _ in range(30):
                prior = rng.integers(0, 3, size=(3, 4))
                witness = rng.integers(0, 4, size=(3, 4))
                if not witness.any():
                    witness[0, 0] = 1
                added_rows = witness.sum(axis=1)
                minimums = np.maximum(0, added_rows - 1)
                maxima = [int(seats + 1) for seats in added_rows]
                targets = (prior + witness).sum(axis=0)
                allocation, _ = switching(
                    rng.uniform(1, 100, size=prior.shape),
                    prior.sum(axis=1) + minimums,
                    targets,
                    prior,
                    rule,
                    num_adjustment_seats=int(added_rows.sum()),
                    min_adj_seats=minimums,
                    max_adj_seats=maxima,
                )
                added = allocation.sum(axis=1) - prior.sum(axis=1)
                self.assertTrue(np.all(allocation >= prior))
                self.assertTrue(np.all(added >= minimums))
                self.assertTrue(np.all(added <= maxima))
                np.testing.assert_array_equal(allocation.sum(axis=0), targets)

    def test_switching_rejects_impossible_protected_seats(self):
        for rows, targets, message in [
                ([2], [1, 1], "party's seat target"),
                ([1], [2, 0], "constituency's seat total")]:
            with self.subTest(rows=rows, targets=targets):
                with self.assertRaisesRegex(ValueError, message):
                    switching([[100, 100]], rows, targets, [[2, 0]],
                              DIVIDER_RULES['sainte-lague'])

    def test_switching_rejects_invalid_divisors(self):
        for sequence in ([2, 1, 3, 4], [0, 1, 2, 3], [1, 2, np.inf, np.inf]):
            with self.subTest(divisors=sequence):
                with self.assertRaisesRegex(ValueError, 'nondecreasing divisors'):
                    switching([[100, 100]], [2], [1, 1], [[0, 0]],
                              lambda: iter(sequence))
