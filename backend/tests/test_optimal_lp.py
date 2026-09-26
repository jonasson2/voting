from itertools import product
import unittest
from unittest.mock import patch

import numpy as np

import entropy_score
from division_rules import dhondt_gen, sainte_lague_gen
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from entropy_score import calculate
from methods.optimal_lp import optimal_lp
from noweb import load_votes
from table_util import entropy


class OptimalLpTest(unittest.TestCase):
    @staticmethod
    def feasible_allocations(prior, total, minimums, maxima, party_deficits):
        prior = np.asarray(prior, dtype=int)
        shape = prior.shape
        for values in product(range(total + 1), repeat=prior.size):
            added = np.asarray(values, dtype=int).reshape(shape)
            if added.sum() != total:
                continue
            if np.any(added.sum(axis=1) < minimums):
                continue
            if np.any(added.sum(axis=1) > maxima):
                continue
            if not np.array_equal(added.sum(axis=0), party_deficits):
                continue
            yield prior + added

    def test_solution_maximizes_entropy_over_all_feasible_allocations(self):
        votes = np.array([[100, 20], [60, 90]])
        prior = np.array([[1, 0], [0, 1]])
        minimums = np.array([0, 1])
        maxima = np.array([2, 2])
        total = 2
        party_targets = np.array([2, 2])

        feasible = list(self.feasible_allocations(
            prior, total, minimums, maxima,
            party_targets - prior.sum(axis=0),
        ))
        for divisor_gen in (dhondt_gen, sainte_lague_gen):
            with self.subTest(divisor=divisor_gen.__name__):
                allocation, _ = optimal_lp(
                    votes, prior.sum(axis=1) + minimums, party_targets,
                    prior, divisor_gen,
                    num_adjustment_seats=total,
                    min_adj_seats=minimums,
                    max_adj_seats=maxima,
                )
                optimum = max(entropy(votes, candidate, divisor_gen)
                              for candidate in feasible)
                self.assertAlmostEqual(
                    entropy(votes, allocation, divisor_gen), optimum)
                self.assertTrue(any(np.array_equal(allocation, candidate)
                                    for candidate in feasible))

    def test_national_seats_leave_party_targets_as_upper_bounds(self):
        allocation, _ = optimal_lp(
            [[100, 20], [60, 90]], [0, 0], [2, 2],
            np.zeros((2, 2), dtype=int), dhondt_gen,
            nat_prior_allocations=[0, 0],
            num_adjustment_seats=2,
            min_adj_seats=[0, 0],
            max_adj_seats=[None, None],
        )

        self.assertEqual(int(allocation.sum()), 2)
        self.assertTrue(np.all(allocation.sum(axis=0) <= [2, 2]))

    def test_party_targets_can_be_omitted_for_unbounded_methods(self):
        allocation, _ = optimal_lp(
            [[100, 1], [90, 1]], [1, 1], [0, 2],
            np.zeros((2, 2), dtype=int), dhondt_gen,
            num_adjustment_seats=2,
            min_adj_seats=[1, 1],
            max_adj_seats=[1, 1],
            enforce_party_targets=False,
        )

        self.assertEqual(allocation.sum(axis=1).tolist(), [1, 1])
        self.assertEqual(allocation.sum(axis=0).tolist(), [2, 0])

    def test_infeasible_constituency_bounds_are_reported(self):
        with self.assertRaisesRegex(ValueError, "maxima prevent"):
            optimal_lp(
                [[100, 20], [60, 90]], [1, 0], [1, 1],
                np.zeros((2, 2), dtype=int), dhondt_gen,
                num_adjustment_seats=2,
                min_adj_seats=[1, 0],
                max_adj_seats=[1, 0],
            )

    def test_method_runs_through_election_handler_with_flexible_rows(self):
        table = load_votes("../data/2-by-2-example.csv")
        table["constituencies"][0].update(
            num_adj_seats=0, max_adj_seats=2)
        table["constituencies"][1].update(
            num_adj_seats=0, max_adj_seats=None)
        table["max_total_adj_seats"] = 3
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        system["adjustment_method"] = "optimal-lp"

        election = ElectionHandler(table, [system], True).elections[0]
        added = (
            np.asarray(election.results["all_const_seats"])
            - np.asarray(election.results["fixed_const_seats"])
        )

        self.assertEqual(int(added.sum()), 3)
        self.assertLessEqual(int(added[0].sum()), 2)

    def test_entropy_score_is_memoized_and_bounded(self):
        table = load_votes("../data/2-by-2-example.csv")
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        system["adjustment_method"] = "max-const-seat-share"
        election = ElectionHandler(table, [system], True).elections[0]
        cache = {}

        with patch(
                "entropy_score._optimal_allocation",
                wraps=entropy_score._optimal_allocation) as solve:
            first = calculate(election, cache)
            second = calculate(election, cache)

        self.assertGreater(first, 0)
        self.assertLessEqual(first, 1)
        self.assertEqual(first, second)
        self.assertEqual(solve.call_count, 1)

    def test_entropy_score_is_the_actual_to_optimal_product_ratio(self):
        table = load_votes("../data/2-by-2-example.csv")
        table["votes"] = [[100, 60], [90, 50]]
        for constituency in table["constituencies"]:
            constituency.update(num_fixed_seats=0, num_adj_seats=1)
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        system["adjustment_method"] = "max-const-votes"
        election = ElectionHandler(table, [system], True).elections[0]

        # Greedy allocation has product 100*50; the optimum has 60*90.
        self.assertAlmostEqual(calculate(election), 5000 / 5400)

    def test_entropy_score_is_unavailable_for_zero_first_divisor_rules(self):
        table = load_votes("../data/2-by-2-example.csv")
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        system["adj_alloc_divider"] = "adams"
        election = ElectionHandler(table, [system], True).elections[0]

        self.assertIsNone(calculate(election))


if __name__ == "__main__":
    unittest.main()
