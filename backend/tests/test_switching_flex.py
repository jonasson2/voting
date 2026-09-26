from itertools import permutations
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from openpyxl import load_workbook

from dictionaries import ADJUSTMENT_METHODS, ADJUSTMENT_METHOD_NAMES, FLEXIBLE_ADJUSTMENT_METHODS
from division_rules import dhondt_gen, sainte_lague_gen
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from methods.max_const_votes import max_const_votes
from methods.switching_flex import switching_flex
from methods.switching_plus import improve_by_exchanges
from noweb import load_votes
from table_util import entropy


def feasible_neighbours(allocation, prior, lower, upper):
    """Enumerate both move types independently of the production search."""
    nconst, nparty = allocation.shape
    for c, d in permutations(range(nconst), 2):
        for p in range(nparty):
            if allocation[c, p] <= prior[c, p]:
                continue
            moved = allocation.copy()
            moved[c, p] -= 1
            moved[d, p] += 1
            rows = moved.sum(axis=1)
            if (rows >= lower).all() and (rows <= upper).all():
                yield moved
            for q in range(nparty):
                if q != p and allocation[d, q] > prior[d, q]:
                    exchanged = moved.copy()
                    exchanged[d, q] -= 1
                    exchanged[c, q] += 1
                    yield exchanged


class SwitchingFlexTest(unittest.TestCase):
    def test_registration_and_order(self):
        names = [item['value'] for item in ADJUSTMENT_METHOD_NAMES]
        start = names.index('switching')
        self.assertEqual(names[start:start + 3],
                         ['switching', 'switching-plus', 'switching-flex'])
        self.assertIs(ADJUSTMENT_METHODS['switching-flex'], switching_flex)
        self.assertIn('switching-flex', FLEXIBLE_ADJUSTMENT_METHODS)

    def test_exchanges_and_moves_choose_the_best_gain_and_can_reassign_minima(self):
        votes = np.array([[84, 93, 34], [1, 68, 80], [15, 26, 17]])
        prior = np.zeros((3, 3), dtype=int)
        bounds = dict(min_adj_seats=[1, 1, 1], max_adj_seats=[4, 4, 4],
                      num_adjustment_seats=7)
        args = votes, [1, 1, 1], [3, 2, 2], prior, dhondt_gen
        initial, _ = max_const_votes(*args, **bounds)
        final, demo = switching_flex(*args, **bounds)
        steps = demo['data']['exchanges']
        self.assertEqual([step['to_party'] for step in steps], [1, 2, None])
        np.testing.assert_array_equal(final, [[2, 1, 0], [0, 1, 2], [1, 0, 0]])
        current = initial.copy()
        for step in steps:
            before = entropy(votes, current, dhondt_gen)
            best = max(entropy(votes, candidate, dhondt_gen)
                       for candidate in feasible_neighbours(current, prior, 1, 4))
            self.assertAlmostEqual(step['log_gain'], best - before)
            c, d = step['from_constituency'], step['to_constituency']
            p, q = step['from_party'], step['to_party']
            current[c, p] -= 1
            current[d, p] += 1
            if q is not None:
                current[d, q] -= 1
                current[c, q] += 1
            self.assertAlmostEqual(entropy(votes, current, dhondt_gen), best)
        np.testing.assert_array_equal(current, final)

    def test_moves_protect_fixed_seats_and_both_row_bounds(self):
        initial = np.array([[3], [0]])
        for lower, upper, prior, expected in [
                ([0, 0], [3, 3], [[0], [0]], [[0], [3]]),
                ([2, 0], [3, 3], [[0], [0]], [[2], [1]]),
                ([0, 0], [3, 1], [[0], [0]], [[2], [1]]),
                ([0, 0], [3, 3], [[2], [0]], [[2], [1]])]:
            with self.subTest(lower=lower, upper=upper, prior=prior):
                final, _ = improve_by_exchanges(
                    [[1], [100]], initial, prior, dhondt_gen,
                    row_bounds=(lower, upper))
                np.testing.assert_array_equal(final, expected)

    def test_equal_gain_does_not_move(self):
        initial = np.array([[1], [0]])
        final, steps = improve_by_exchanges(
            [[100], [100]], initial, np.zeros_like(initial), dhondt_gen,
            row_bounds=([0, 0], [1, 1]))
        np.testing.assert_array_equal(final, initial)
        self.assertEqual(steps, [])

    def test_exact_bounds_allow_exchanges_but_not_moves(self):
        final, demo = switching_flex(
            [[84, 93, 34], [1, 68, 80], [15, 26, 17]],
            [3, 3, 1], [3, 2, 2], np.zeros((3, 3), dtype=int), dhondt_gen)
        np.testing.assert_array_equal(final.sum(axis=1), [3, 3, 1])
        self.assertTrue(all(step['to_party'] is not None
                            for step in demo['data']['exchanges']))

    def test_zero_votes_unlimited_bounds_and_national_fixed_seats(self):
        final, _ = switching_flex(
            [[0, 0], [100, 0]], [1, 0], [2, 2], [[1, 0], [0, 0]],
            dhondt_gen, num_adjustment_seats=2,
            min_adj_seats=[0, 0], max_adj_seats=[None, None],
            nat_prior_allocations=[0, 1])
        np.testing.assert_array_equal(final.sum(axis=0), [2, 1])
        self.assertGreaterEqual(final[0, 0], 1)

    def test_random_small_problems_finish_at_a_local_optimum(self):
        rng = np.random.default_rng(321)
        for rule in (dhondt_gen, sainte_lague_gen):
            for _ in range(12):
                votes = rng.integers(1, 101, size=(3, 3))
                prior = rng.integers(0, 2, size=(3, 3))
                lower = prior.sum(axis=1) + [1, 0, 0]
                upper = prior.sum(axis=1) + [2, 3, 4]
                targets = prior.sum(axis=0) + [2, 2, 1]
                final, _ = switching_flex(
                    votes, lower, targets, prior, rule,
                    min_adj_seats=[1, 0, 0], max_adj_seats=[2, 3, 4],
                    num_adjustment_seats=5)
                np.testing.assert_array_equal(final.sum(axis=0), targets)
                self.assertTrue((final >= prior).all())
                self.assertTrue((final.sum(axis=1) >= lower).all())
                self.assertTrue((final.sum(axis=1) <= upper).all())
                score = entropy(votes, final, rule)
                for candidate in feasible_neighbours(final, prior, lower, upper):
                    self.assertLessEqual(entropy(votes, candidate, rule), score + 1e-10)

    def test_election_and_excel_include_both_step_tables(self):
        table = load_votes('../data/2-by-2-example.csv')
        for constituency in table['constituencies']:
            constituency.update(num_adj_seats=0, max_adj_seats=None)
        table['max_total_adj_seats'] = 4
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        system.update(name='Flexible switching', adjustment_method='switching-flex')
        handler = ElectionHandler(table, [system], True)
        tables = handler.elections[0].demo_tables
        self.assertEqual(len(tables), 2)
        for demo in tables:
            self.assertEqual(len(demo['headers']), len(demo['format']))
            self.assertTrue(all(len(row) == len(demo['headers']) for row in demo['steps']))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'switching-flex.xlsx'
            handler.to_xlsx(path)
            book = load_workbook(path)
            text = [cell.value for sheet in book for row in sheet for cell in row]
            self.assertIn('Improving exchanges and moves', text)
            book.close()


if __name__ == '__main__':
    unittest.main()
