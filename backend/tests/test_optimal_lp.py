from itertools import product
import unittest

import numpy as np

from division_rules import dhondt_gen, sainte_lague_gen
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
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


if __name__ == "__main__":
    unittest.main()
