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
