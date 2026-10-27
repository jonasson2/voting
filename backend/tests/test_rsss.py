"""Check RSSS objectives against exhaustive allocations, not solver internals."""

from itertools import product
import unittest

import numpy as np

from dictionaries import ADJUSTMENT_METHODS
from division_rules import dhondt_gen, sainte_lague_gen
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from input_files import load_votes
from simulate import SimulationSettings
from simulation_chunks import run_chunk, combine_chunks


METHODS = {key: method for key, method in ADJUSTMENT_METHODS.items()
           if key.startswith('rsss-') and '-switching-' not in key}


class RsssTest(unittest.TestCase):
    def test_objectives_against_exhaustive_allocations(self):
        # q has row/column totals 2. Multiplying rows and columns of it
        # preserves its known double-scaled reference, but changes local shares.
        q = np.array([[1.2, .5, .3], [.2, 1.1, .7], [.6, .4, 1.]])
        votes = q * np.array([7., 1., 3.])[:, None] * [1., 4., 2.]
        local = votes / votes.sum(1)[:, None] * 2
        row_choices = [r for r in product(range(3), repeat=3) if sum(r) == 2]
        candidates = [np.array(a) for a in product(row_choices, repeat=3)
                      if np.array_equal(np.sum(a, axis=0), [2, 2, 2])]
        for name, method in METHODS.items():
            power = 1 if 'minl1' in name else 2
            reference = q if name.endswith('double') else local
            for prior in (np.zeros((3, 3), int), np.eye(3, dtype=int)):
                feasible = [a for a in candidates if (a >= prior).all()]
                objective = lambda a: float((abs(a - reference) ** power).sum())
                for rule in (dhondt_gen, sainte_lague_gen):
                    with self.subTest(method=name, prior=prior.tolist(), rule=rule.__name__):
                        allocation, _ = method(votes, [2]*3, [2]*3, prior, rule)
                        self.assertTrue(any(np.array_equal(allocation, a) for a in feasible))
                        self.assertAlmostEqual(objective(allocation), min(map(objective, feasible)))

    def test_sparse_votes_zero_rows_and_fixed_seats(self):
        for method in METHODS.values():
            allocation, _ = method([[0, 0], [0, 30]], [0, 2], [0, 2],
                                   [[0, 0], [0, 1]])
            np.testing.assert_array_equal(allocation, [[0, 0], [0, 2]])
            with self.assertRaises(ValueError):
                method([[100, 0]], [1], [0, 1], [[0, 0]])
            with self.assertRaisesRegex(ValueError, 'fixed constituency'):
                method([[50, 50]], [0], [1, 1], [[0, 0]],
                       num_adjustment_seats=2, min_adj_seats=[0], max_adj_seats=[None])

    def test_national_fixed_seats_are_not_constituency_targets(self):
        for method in METHODS.values():
            allocation, _ = method([[60, 40], [30, 70]], [2, 2], [3, 2],
                                   [[0, 0], [0, 0]], nat_prior_allocations=[1, 0])
            np.testing.assert_array_equal(allocation.sum(0), [2, 2])

    def test_election_and_simulation_pipeline(self):
        table = load_votes('../data/2-by-2-example.csv')
        systems = []
        for method in ADJUSTMENT_METHODS:
            if not method.startswith('rsss-'):
                continue
            system = ElectionSystem()
            system.copy_info_from_votes(table)
            system.update(name=method, adjustment_method=method)
            systems.append(system)
        handler = ElectionHandler(table, systems, True)
        self.assertEqual(len(handler.elections), 8)
        settings = dict(SimulationSettings(), simulation_count=2, cpu_count=1,
                        random_seed=123, sensitivity=True, sensitivity_simulation_count=2,
                        sensitivity_covs=[.01], single_list_sensitivity=False)
        result = combine_chunks([run_chunk(table, systems, settings, 2, 0)])
        self.assertEqual(len(result.data), 8)
        for data in result.data:
            self.assertTrue(np.isfinite(data['local_squared']['avg']))
