"""Independently evaluate RSSS switches and their feasible neighbours."""

from itertools import permutations
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from openpyxl import load_workbook

from dictionaries import ADJUSTMENT_METHODS
from division_rules import dhondt_gen, danish_gen
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from input_files import load_votes
from methods.rsss import marginal_costs
from methods.seat_switching import improve_by_costs
from tests.test_switching_flex import feasible_neighbours


METHODS = {key: method for key, method in ADJUSTMENT_METHODS.items()
           if key.startswith('rsss-') and '-switching-' in key}


class RsssSwitchingTest(unittest.TestCase):
    def test_each_exchange_is_best_and_stops_at_local_optimum(self):
        rng = np.random.default_rng(912)
        permutations_matrices = np.array([np.eye(3)[list(order)]
                                         for order in permutations(range(3))])
        steps_seen = 0
        for _ in range(12):
            weights = rng.random(6)
            # Known double-scaled reference: every margin equals 2.
            q = .1 + 1.7 * np.einsum('i,ijk->jk', weights / weights.sum(), permutations_matrices)
            votes = q * rng.uniform(.1, 10, (3, 1)) * rng.uniform(.1, 10, (1, 3))
            local = votes / votes.sum(1)[:, None] * 2
            prior = np.eye(3, dtype=int)
            for name, method in METHODS.items():
                reference = q if name.endswith('double') else local
                power = 1 if 'minl1' in name else 2
                objective = lambda a: float((abs(a - reference) ** power).sum())
                final, demo = method(votes, [2]*3, [2]*3, prior, dhondt_gen)
                current = prior.copy()
                for step in demo['data']['initial']['data']['sequence']:
                    current[step['constituency'], step['party']] += 1
                for step in demo['data']['exchanges']:
                    steps_seen += 1
                    before = objective(current)
                    best = min(objective(a) for a in feasible_neighbours(current, prior, 2, 2))
                    self.assertAlmostEqual(step['reduction'], before - best)
                    self.assertGreater(step['reduction'], 0)
                    c, d = step['from_constituency'], step['to_constituency']
                    p, r = step['from_party'], step['to_party']
                    current[c, p] -= 1; current[d, p] += 1
                    current[d, r] -= 1; current[c, r] += 1
                    self.assertAlmostEqual(objective(current), best)
                np.testing.assert_array_equal(current, final)
                np.testing.assert_array_equal(final.sum(0), [2]*3)
                np.testing.assert_array_equal(final.sum(1), [2]*3)
                self.assertTrue((final >= prior).all())
                for neighbour in feasible_neighbours(final, prior, 2, 2):
                    self.assertGreaterEqual(objective(neighbour) + 1e-10, objective(final))
                exact, _ = ADJUSTMENT_METHODS[name.replace('-switching', '')](
                    votes, [2]*3, [2]*3, prior, dhondt_gen)
                self.assertGreaterEqual(objective(final) + 1e-10, objective(exact))
        self.assertGreater(steps_seen, 0)

    def test_sparse_greedy_dead_end_uses_feasibility_lp(self):
        for power in (1, 2):
            method = METHODS[f'rsss-minl{power}-switching-const']
            final, demo = method([[6, 4, 0], [6, 4, 0], [7, 0, 3]],
                                 [1]*3, [1]*3, np.zeros((3, 3), int))
            self.assertIsNone(demo['data']['initial'])
            np.testing.assert_array_equal(final.sum(0), [1]*3)
            np.testing.assert_array_equal(final.sum(1), [1]*3)
            self.assertEqual(final[0, 2] + final[1, 2] + final[2, 1], 0)

    def test_no_equal_cost_switches_and_divisor_is_ignored(self):
        prior = np.zeros((2, 2), int)
        for power in (1, 2):
            start = np.eye(2, dtype=int)
            final, steps = improve_by_costs(start, prior,
                lambda seats: marginal_costs(np.full((2, 2), .5), seats, power))
            np.testing.assert_array_equal(final, start)
            self.assertEqual(steps, [])
        for method in METHODS.values():
            a, _ = method([[20, 80], [70, 30]], [2, 2], [2, 2], prior, dhondt_gen)
            b, _ = method([[20, 80], [70, 30]], [2, 2], [2, 2], prior, danish_gen)
            np.testing.assert_array_equal(a, b)
            with self.assertRaisesRegex(ValueError, 'fixed constituency'):
                method([[20, 80], [70, 30]], [0, 0], [2, 2], prior,
                       min_adj_seats=[0, 0], max_adj_seats=[None, None], num_adjustment_seats=4)

    def test_report_tables_and_excel(self):
        votes = load_votes('../data/2-by-2-example.csv')
        systems = []
        for name in METHODS:
            system = ElectionSystem()
            system.copy_info_from_votes(votes)
            system.update(adjustment_method=name, name=name)
            systems.append(system)
        handler = ElectionHandler(votes, systems, True)
        for election in handler.elections:
            for table in election.demo_tables:
                self.assertTrue(all(len(row) == len(table['format']) for row in table['steps']))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'rsss.xlsx'
            handler.to_xlsx(path)
            workbook = load_workbook(path)
            text = [cell.value for sheet in workbook for row in sheet for cell in row]
            self.assertIn('Objective reduction', text)
            workbook.close()

    def test_zero_rows_national_fixed_seats_and_regions(self):
        for method in METHODS.values():
            final, _ = method([[0, 0], [0, 30]], [0, 2], [1, 2],
                              [[0, 0], [0, 1]], nat_prior_allocations=[1, 0])
            np.testing.assert_array_equal(final, [[0, 0], [0, 2]])
        import csv
        from vote_table import check_vote_table, process_vote_table
        rows = csv.reader([
            'Example,fixed,adj,region,A,B',
            'North 1,2,1,N,70,30', 'South 1,3,1,S,60,40',
            'North 2,1,1,N,20,80', 'South 2,1,1,S,30,70',
            ',,,,,', 'Regions,Name,adj,,,', 'N,North,2,,,', 'S,South,2,,,',
        ])
        votes = check_vote_table(process_vote_table(list(rows), 'test.csv'))
        for name in METHODS:
            system = ElectionSystem()
            system.copy_info_from_votes(votes)
            system.update(adjustment_method=name)
            election = ElectionHandler(votes, [system], True).elections[0]
            allocation = np.asarray(election.results['all_const_seats'])
            for group, target in zip(election.region_groups, election.region_party_totals):
                np.testing.assert_array_equal(allocation[group].sum(0), target)
