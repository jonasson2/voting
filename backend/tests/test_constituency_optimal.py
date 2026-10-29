"""Compare constituency-protected logarithmic optima with exhaustive solutions."""

from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from openpyxl import load_workbook

from dictionaries import ADJUSTMENT_METHODS, FLEXIBLE_ADJUSTMENT_METHODS
from division_rules import dhondt_gen, sainte_lague_gen
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from input_files import load_votes
from methods.optimal_lp import optimal_lp
from methods.provisional_allocation import allocate_provisionally
from methods.seat_lp import allocate_by_marginal_costs
from simulate import SimulationSettings
from simulation_chunks import run_chunk, combine_chunks
from table_util import entropy


METHODS = {key: ADJUSTMENT_METHODS[key]
           for key in ('optimal-exact-parties', 'optimal-one-way')}


class ConstituencyOptimalTest(unittest.TestCase):
    def test_optima_against_exhaustive_allocations(self):
        row_choices = [r for r in product(range(4), repeat=3) if sum(r) == 3]
        candidates = [np.array(a) for a in product(row_choices, repeat=3)
                      if np.array_equal(np.sum(a, axis=0), [3]*3)]
        tables = [
            [[99, 90, 4], [72, 116, 47], [149, 3, 77]],
            [[52, 116, 139], [139, 130, 30], [104, 33, 4]],
            [[20, 80, 10], [60, 30, 90], [50, 40, 70]],
        ]
        for votes, rule, prior in product(
                tables, (dhondt_gen, sainte_lague_gen),
                (np.eye(3, dtype=int), np.zeros((3, 3), int))):
            baseline = allocate_provisionally(votes, [3]*3, prior, rule)
            difference = baseline.sum(0) - 3
            for name, method in METHODS.items():
                feasible = [a for a in candidates if (a >= prior).all()
                            and np.array_equal(a[:, difference == 0],
                                               baseline[:, difference == 0])]
                if name == 'optimal-one-way':
                    feasible = [a for a in feasible
                                if (a[:, difference > 0] <= baseline[:, difference > 0]).all()
                                and (a[:, difference < 0] >= baseline[:, difference < 0]).all()]
                with self.subTest(method=name, votes=votes, rule=rule.__name__):
                    allocation, _ = method(votes, [3]*3, [3]*3, prior, rule)
                    self.assertTrue(any(np.array_equal(allocation, a) for a in feasible))
                    self.assertAlmostEqual(
                        entropy(votes, allocation, rule),
                        max(entropy(votes, a, rule) for a in feasible))

    def test_both_restrictions_can_strictly_reduce_the_optimum(self):
        prior = np.eye(3, dtype=int)
        for votes, strict_pair in (
                ([[99, 90, 4], [72, 116, 47], [149, 3, 77]], 0),
                ([[52, 116, 139], [139, 130, 30], [104, 33, 4]], 1)):
            scores = [entropy(votes, method(votes, [3]*3, [3]*3, prior,
                                          dhondt_gen)[0], dhondt_gen)
                      for method in (optimal_lp, *METHODS.values())]
            self.assertGreater(scores[strict_pair], scores[strict_pair + 1] + 1e-8)
            self.assertGreaterEqual(scores[0] + 1e-8, scores[1])
            self.assertGreaterEqual(scores[1] + 1e-8, scores[2])

    def test_worked_example_and_national_fixed_seats(self):
        for method in METHODS.values():
            for targets, options in (([3, 3, 2], {}),
                                     ([4, 3, 2], {'nat_prior_allocations': [1, 0, 0]})):
                allocation, _ = method(
                    [[100, 40, 90], [60, 55, 100]], [4, 4], targets,
                    [[1, 0, 0], [1, 0, 0]], dhondt_gen, **options)
                np.testing.assert_array_equal(allocation, [[2, 1, 1], [1, 2, 1]])

    def test_zero_rows_vote_floor_and_deterministic_baseline_ties(self):
        for method in METHODS.values():
            allocation, _ = method([[0, 0], [0, 30]], [0, 2], [0, 2],
                                   [[0, 0], [0, 1]], dhondt_gen)
            np.testing.assert_array_equal(allocation, [[0, 0], [0, 2]])
            # Same vote floor as the classical entropy optimum; all seats fixed.
            allocation, _ = method([[0, .5]], [2], [1, 1], [[1, 1]], dhondt_gen)
            np.testing.assert_array_equal(allocation, [[1, 1]])
            for _ in range(2):
                allocation, _ = method([[10, 10], [10, 10]], [1, 1], [2, 0],
                                       np.zeros((2, 2), int), dhondt_gen)
                np.testing.assert_array_equal(allocation, [[1, 0], [1, 0]])

    def test_row_scaling_preserves_baseline_and_optimum(self):
        votes = np.array([[99, 90, 4], [72, 116, 47], [149, 3, 77]])
        prior = np.eye(3, dtype=int)
        for method in METHODS.values():
            a, _ = method(votes, [3]*3, [3]*3, prior, dhondt_gen)
            # Row scaling preserves the independent baseline, hence its bounds.
            b, _ = method(votes * np.array([2, 7, 3])[:, None],
                          [3]*3, [3]*3, prior, dhondt_gen)
            np.testing.assert_array_equal(a, b)

    def test_rejects_flexible_totals_and_unallocated_national_seats(self):
        for name, method in METHODS.items():
            self.assertNotIn(name, FLEXIBLE_ADJUSTMENT_METHODS)
            with self.assertRaisesRegex(ValueError, 'fixed constituency totals'):
                method([[50, 50]], [0], [1, 1], [[0, 0]], dhondt_gen,
                       num_adjustment_seats=2, min_adj_seats=[0], max_adj_seats=[None])
            with self.assertRaisesRegex(ValueError, 'national adjustment seats'):
                method([[50, 50]], [1], [1, 1], [[0, 0]], dhondt_gen)

    def test_shared_lp_rejects_invalid_and_infeasible_list_bounds(self):
        options = dict(row_totals=[1, 1], party_totals=[1, 1],
                       prior=np.zeros((2, 2), int),
                       marginal_costs=lambda variables: np.zeros(len(variables)))
        for bounds in (
                {'list_lower_bounds': [[.5, 0], [0, 0]]},
                {'list_upper_bounds': [[-1, 0], [1, 1]]},
                {'list_lower_bounds': [[1, 1], [0, 0]]},
                {'list_lower_bounds': [[1, 0], [1, 0]]},
                {'list_upper_bounds': [[1, 0], [1, 0]]}):
            with self.subTest(bounds=bounds), self.assertRaises(ValueError):
                allocate_by_marginal_costs(**options, **bounds)

    def test_election_simulation_and_excel_pipeline(self):
        table = load_votes('../data/2-by-2-example.csv')
        systems = []
        for name in METHODS:
            system = ElectionSystem()
            system.copy_info_from_votes(table)
            system.update(name=name, adjustment_method=name)
            systems.append(system)
        handler = ElectionHandler(table, systems, True)
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'protected.xlsx'
            handler.to_xlsx(path)
            workbook = load_workbook(path)
            text = [cell.value for sheet in workbook for row in sheet for cell in row]
            self.assertIn('Exactly represented parties intact', text)
            self.assertIn('One-way maximisation', text)
            workbook.close()
        settings = dict(SimulationSettings(), simulation_count=2, cpu_count=1,
                        random_seed=123, sensitivity=True, sensitivity_simulation_count=2,
                        sensitivity_covs=[.01], single_list_sensitivity=False)
        result = combine_chunks([run_chunk(table, systems, settings, 2, 0)])
        self.assertEqual(len(result.data), 2)
        for data in result.data:
            self.assertTrue(np.isfinite(data['local_squared']['avg']))
