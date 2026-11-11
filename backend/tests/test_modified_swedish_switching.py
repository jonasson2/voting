"""Check recipients-first choices against exhaustive feasible donor plans."""

from itertools import product
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
from methods.constituency_optimal import one_way
from methods.modified_swedish_switching import switching
from methods.provisional_allocation import allocate_provisionally, divisor_values
from methods.swedish_style_switching import switching as original
from simulate import SimulationSettings
from simulation_chunks import run_chunk, combine_chunks
from table_util import entropy


def removal_plans(baseline, prior, targets):
    """Enumerate all ways of removing precisely each O-party's surplus."""
    columns = []
    for p, difference in enumerate(baseline.sum(0) - targets):
        surplus = max(0, int(difference))
        columns.append([x for x in product(range(surplus + 1), repeat=len(baseline))
                        if sum(x) == surplus
                        and np.all(x <= baseline[:, p] - prior[:, p])])
    return np.array([np.array(columns).T for columns in product(*columns)])


class ModifiedSwedishSwitchingTest(unittest.TestCase):
    def test_recipients_first_differs_from_donors_first(self):
        votes = [[5, 27, 24], [10, 28, 1], [13, 15, 21]]
        prior = [[0, 1, 0], [0, 1, 0], [0, 0, 1]]
        args = (votes, [5]*3, [3, 7, 5], prior, dhondt_gen)
        final, report = switching(*args)
        np.testing.assert_array_equal(final, [[0, 2, 3], [1, 4, 0], [2, 1, 2]])
        np.testing.assert_array_equal(original(*args)[0],
                                      [[0, 3, 2], [2, 3, 0], [1, 1, 3]])
        self.assertEqual(report['data']['additions'], [
            {'constituency': 0, 'to': 2, 'recipient_quotient': 8.0},
            {'constituency': 2, 'to': 0, 'recipient_quotient': 6.5}])
        self.assertEqual(report['data']['removals'], [
            {'constituency': 2, 'from': 1, 'removal_quotient': 7.5},
            {'constituency': 0, 'from': 1, 'removal_quotient': 9.0}])

    def test_additions_and_removals_cannot_exhaust_the_wrong_donor(self):
        # Constituency 3 has two removable C seats, but C's surplus is only one.
        votes = [[13, 8, 41, 3], [26, 3, 23, 4], [2, 21, 48, 50]]
        prior = [[0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 1]]
        final, report = switching(votes, [5]*3, [2, 2, 7, 4], prior, dhondt_gen)
        additions = report['data']['additions']
        self.assertEqual(sum(step['constituency'] == 2 for step in additions), 1)
        self.assertEqual([(step['constituency'], step['to']) for step in additions],
                         [(2, 3), (0, 1), (1, 3)])
        # C's weakest seat is in constituency 1, but its only removal must
        # occur in constituency 3, where A has no seats available to give.
        self.assertEqual([(step['constituency'], step['from'])
                          for step in report['data']['removals']],
                         [(1, 0), (0, 0), (2, 2)])
        np.testing.assert_array_equal(final, [[0, 1, 4, 0], [2, 0, 2, 1], [0, 1, 1, 3]])
        np.testing.assert_array_equal(final.sum(0), [2, 2, 7, 4])
        np.testing.assert_array_equal(final.sum(1), [5]*3)

    def test_greedy_choices_preserve_a_feasible_completion(self):
        rng = np.random.default_rng(206)
        prior, targets = np.eye(3, 4, dtype=int), np.array([4, 4, 4, 3])
        for rule in (dhondt_gen, sainte_lague_gen, danish_gen):
            for _ in range(40):
                votes = rng.integers(1, 1000, (3, 4))
                baseline = allocate_provisionally(votes, [5]*3, prior, rule)
                plans = removal_plans(baseline, prior, targets)
                final, report = switching(votes, [5]*3, targets, prior, rule)
                current, excess = baseline.copy(), np.zeros(3, int)
                divisors = divisor_values(rule, 5)
                for step in report['data']['additions']:
                    scores = votes / divisors[current]
                    scores[:, current.sum(0) >= targets] = -np.inf
                    scores[excess >= plans.max(axis=0).sum(1), :] = -np.inf
                    for c in range(3):
                        required = excess.copy()
                        required[c] += 1
                        if not (plans.sum(2) >= required).all(axis=1).any():
                            scores[c, :] = -np.inf
                    c, p = np.unravel_index(scores.argmax(), scores.shape)
                    self.assertEqual((step['constituency'], step['to']), (c, p))
                    self.assertAlmostEqual(step['recipient_quotient'], scores[c, p])
                    current[c, p] += 1
                    excess[c] += 1
                plans = plans[(plans.sum(2) == excess).all(axis=1)]
                self.assertGreater(len(plans), 0)
                removed = np.zeros_like(prior)
                for step in report['data']['removals']:
                    scores = votes / divisors[np.maximum(current - 1, 0)]
                    scores[(current <= prior) | (current.sum(0) <= targets)[None, :]
                           | (excess == 0)[:, None]] = np.inf
                    for c, p in np.ndindex(current.shape):
                        candidate = removed.copy()
                        candidate[c, p] += 1
                        if not (plans >= candidate).all(axis=(1, 2)).any():
                            scores[c, p] = np.inf
                    c, p = np.unravel_index(scores.argmin(), scores.shape)
                    self.assertEqual((step['constituency'], step['from']), (c, p))
                    self.assertAlmostEqual(step['removal_quotient'], scores[c, p])
                    current[c, p] -= 1
                    removed[c, p] += 1
                    excess[c] -= 1
                np.testing.assert_array_equal(current, final)
                np.testing.assert_array_equal(final.sum(0), targets)
                np.testing.assert_array_equal(final.sum(1), [5]*3)
                difference = baseline.sum(0) - targets
                self.assertEqual(abs(final - baseline).sum(), abs(difference).sum())
                self.assertTrue((final >= prior).all())
                optimum, _ = one_way(votes, [5]*3, targets, prior, rule)
                self.assertLessEqual(entropy(votes, final, rule),
                                     entropy(votes, optimum, rule) + 1e-10)

    def test_ties_no_changes_and_unsupported_bounds(self):
        self.assertIs(ADJUSTMENT_METHODS['modified-swedish-switching'], switching)
        self.assertNotIn('modified-swedish-switching', FLEXIBLE_ADJUSTMENT_METHODS)
        reports = []
        args = ([[10, 10], [10, 10]], [1, 1], [1, 1], np.zeros((2, 2), int),
                dhondt_gen)
        first, _ = switching(*args, on_tie=lambda *event: reports.append(event))
        np.testing.assert_array_equal(first, [[0, 1], [1, 0]])
        np.testing.assert_array_equal(switching(*args)[0], first)
        self.assertTrue(reports)
        final, report = switching([[0, .5], [0, 30]], [0, 2], [1, 2],
                                  [[0, 0], [0, 1]], dhondt_gen,
                                  nat_prior_allocations=[1, 0])
        np.testing.assert_array_equal(final, [[0, 0], [0, 2]])
        self.assertEqual(report['data']['additions'], [])
        self.assertEqual(report['data']['removals'], [])
        with self.assertRaisesRegex(ValueError, 'fixed constituency totals'):
            switching([[50, 50]], [0], [1, 1], [[0, 0]], dhondt_gen,
                      num_adjustment_seats=2, min_adj_seats=[0], max_adj_seats=[None])
        with self.assertRaisesRegex(ValueError, 'national adjustment seats'):
            switching([[50, 50]], [1], [1, 1], [[0, 0]], dhondt_gen)

    def test_reports_and_simulation(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['votes'] = [[60, 40], [20, 80]]
        for constituency in table['constituencies']:
            constituency.update(num_fixed_seats=2, num_adj_seats=2)
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        system.update(name='One-way recipients first',
                      adjustment_method='modified-swedish-switching',
                      primary_divider='dhondt', constituency_threshold=50,
                      fixed_seat_threshold_choice=0, adj_alloc_divider='sainte-lague')
        handler = ElectionHandler(table, [system], True)
        election = handler.elections[0]
        np.testing.assert_array_equal(election.results['fixed_const_seats'], [[2, 0], [0, 2]])
        self.assertEqual(len(election.demo_tables), 3)
        for report in election.demo_tables:
            self.assertTrue(all(len(row) == len(report['format']) for row in report['steps']))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'modified-swedish.xlsx'
            handler.to_xlsx(path)
            workbook = load_workbook(path)
            text = [cell.value for sheet in workbook for row in sheet for cell in row]
            self.assertIn('Addition of missing adjustment seats', text)
            self.assertIn('Removal of excess adjustment seats', text)
            workbook.close()
        settings = dict(SimulationSettings(), simulation_count=2, cpu_count=1,
                        random_seed=123, sensitivity=True, sensitivity_simulation_count=2,
                        sensitivity_covs=[.1], single_list_sensitivity=False)
        result = combine_chunks([run_chunk(table, [system], settings, 2, 0)])
        self.assertEqual(len(result.data), 1)
