"""Verify original O/U bounds, greedy choices and the reporting pipeline."""
from itertools import permutations
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from openpyxl import load_workbook

from dictionaries import ADJUSTMENT_METHODS, FLEXIBLE_ADJUSTMENT_METHODS
from division_rules import dhondt_gen, sainte_lague_gen, danish_gen
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from input_files import load_votes
from methods.adjustment_as_fixed import adjustment_as_fixed
from methods.constituency_optimal import one_way
from methods.one_way_switching import one_way_switching, simple_one_way_switching
from simulate import SimulationSettings
from simulation_chunks import run_chunk, combine_chunks
from table_util import entropy

METHODS = ('simple-one-way-switching', 'one-way-switching')


class OneWaySwitchingTest(unittest.TestCase):
    def test_greedy_choices_and_restricted_local_optimum(self):
        rng = np.random.default_rng(735)
        prior = np.eye(3, 4, dtype=int)
        targets = np.array([4, 4, 4, 3])
        rectangles_seen = exact_seen = 0
        for rule in (dhondt_gen, sainte_lague_gen, danish_gen):
            for _ in range(20):
                votes = rng.integers(1, 1000, (3, 4))
                baseline, _ = adjustment_as_fixed(votes, [5]*3, targets, prior, rule)
                difference = baseline.sum(0) - targets
                exact_seen += int((difference == 0).any())
                lower = np.where((difference > 0)[None, :], prior, baseline)
                upper = np.where((difference < 0)[None, :], 5, baseline)
                score = lambda a: entropy(votes, a, rule)
                simple, _ = simple_one_way_switching(votes, [5]*3, targets, prior, rule)
                final, demo = one_way_switching(votes, [5]*3, targets, prior, rule)
                current = baseline.copy()
                for step in demo['data']['switches']:
                    balance = current.sum(0) - targets
                    scores = []
                    for c in range(3):
                        for p in np.flatnonzero(balance > 0):
                            if current[c, p] <= prior[c, p]:
                                continue
                            for q in np.flatnonzero(balance < 0):
                                candidate = current.copy()
                                candidate[c, p] -= 1
                                candidate[c, q] += 1
                                scores.append(score(candidate))
                    before = score(current)
                    current[step['constituency'], step['from']] -= 1
                    current[step['constituency'], step['to']] += 1
                    self.assertAlmostEqual(score(current), max(scores))
                    self.assertAlmostEqual(np.log(step['ratio']), before - score(current))
                np.testing.assert_array_equal(current, simple)

                def neighbour_scores():
                    for c, d in permutations(range(3), 2):
                        for p in np.flatnonzero(difference > 0):
                            for q in np.flatnonzero(difference < 0):
                                candidate = current.copy()
                                candidate[c, p] -= 1
                                candidate[d, p] += 1
                                candidate[d, q] -= 1
                                candidate[c, q] += 1
                                if (candidate >= lower).all() and (candidate <= upper).all():
                                    yield score(candidate)

                for step in demo['data']['exchanges']:
                    rectangles_seen += 1
                    best = max(neighbour_scores(), default=score(current))
                    before = score(current)
                    c, d = step['from_constituency'], step['to_constituency']
                    p, q = step['from_party'], step['to_party']
                    self.assertLess(difference[p] * difference[q], 0)
                    current[c, p] -= 1
                    current[d, p] += 1
                    current[d, q] -= 1
                    current[c, q] += 1
                    self.assertAlmostEqual(score(current), best)
                    self.assertAlmostEqual(score(current) - before, step['log_gain'])
                    self.assertGreater(step['log_gain'], 0)
                np.testing.assert_array_equal(current, final)
                self.assertTrue((final >= lower).all() and (final <= upper).all())
                np.testing.assert_array_equal(final.sum(0), targets)
                np.testing.assert_array_equal(final.sum(1), [5]*3)
                self.assertLessEqual(max(neighbour_scores(), default=score(final)),
                                     score(final) + 1e-10)
                optimum, _ = one_way(votes, [5]*3, targets, prior, rule)
                self.assertLessEqual(score(final), score(optimum) + 1e-10)
        self.assertGreater(rectangles_seen, 0)
        self.assertGreater(exact_seen, 0)

    def test_edge_cases_and_unsupported_bounds(self):
        for name in METHODS:
            method = ADJUSTMENT_METHODS[name]
            self.assertNotIn(name, FLEXIBLE_ADJUSTMENT_METHODS)
            a, _ = method([[0, .5], [0, 30]], [0, 2], [1, 2],
                          [[0, 0], [0, 1]], dhondt_gen,
                          nat_prior_allocations=[1, 0])
            np.testing.assert_array_equal(a, [[0, 0], [0, 2]])
            for _ in range(2):
                a, _ = method([[10, 10], [10, 10]], [1, 1], [2, 0],
                              np.zeros((2, 2), int), dhondt_gen)
                np.testing.assert_array_equal(a, [[1, 0], [1, 0]])
            with self.assertRaisesRegex(ValueError, 'fixed constituency totals'):
                method([[50, 50]], [0], [1, 1], [[0, 0]], dhondt_gen,
                       num_adjustment_seats=2, min_adj_seats=[0], max_adj_seats=[None])
            with self.assertRaisesRegex(ValueError, 'national adjustment seats'):
                method([[50, 50]], [1], [1, 1], [[0, 0]], dhondt_gen)
            with self.assertRaisesRegex(ValueError, 'protected fixed seats'):
                method([[50, 50]], [2], [0, 2], [[1, 0]], dhondt_gen)

    def test_fixed_rules_baseline_reports_and_simulation(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['votes'] = [[60, 40], [20, 80]]
        for constituency in table['constituencies']:
            constituency.update(num_fixed_seats=2, num_adj_seats=2)
        systems = []
        for name in ('adjustment-as-fixed', 'optimal-one-way', *METHODS):
            system = ElectionSystem()
            system.copy_info_from_votes(table)
            system.update(name=name, adjustment_method=name, primary_divider='dhondt',
                          constituency_threshold=50, fixed_seat_threshold_choice=0,
                          adj_alloc_divider='sainte-lague')
            systems.append(system)
        handler = ElectionHandler(table, systems, True)
        baseline = handler.elections[0].results['all_const_seats']
        for election in handler.elections:
            np.testing.assert_array_equal(election.results['fixed_const_seats'], [[2, 0], [0, 2]])
        for election in handler.elections[2:]:
            initial = election.demo_tables[0]['steps']
            np.testing.assert_array_equal([row[2] for row in initial], np.sum(baseline, axis=0))
            for report in election.demo_tables:
                self.assertTrue(all(len(row) == len(report['format']) for row in report['steps']))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'one-way.xlsx'
            handler.to_xlsx(path)
            workbook = load_workbook(path)
            text = [cell.value for sheet in workbook for row in sheet for cell in row]
            self.assertIn('One-way switching', text)
            self.assertIn('Simple one-way switching', text)
            workbook.close()
        settings = dict(SimulationSettings(), simulation_count=2, cpu_count=1,
                        random_seed=123, sensitivity=True, sensitivity_simulation_count=2,
                        sensitivity_covs=[.1], single_list_sensitivity=False)
        result = combine_chunks([run_chunk(table, systems[2:], settings, 2, 0)])
        self.assertEqual(len(result.data), 2)
