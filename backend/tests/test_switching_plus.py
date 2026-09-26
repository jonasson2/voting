from math import log
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from openpyxl import load_workbook

from dictionaries import ADJUSTMENT_METHODS, FLEXIBLE_ADJUSTMENT_METHODS
from division_rules import dhondt_gen
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from methods.switching import switching
from methods.switching_plus import improve_by_exchanges, switching_plus
from noweb import load_votes
from table_util import entropy


class SwitchingPlusTest(unittest.TestCase):
    def test_exchange_improves_normal_switching_and_preserves_both_margins(self):
        votes = np.array([[1000, 500, 200], [500, 600, 800], [1000, 900, 400]])
        prior = np.zeros((3, 3), dtype=int)
        normal, original_demo = switching(votes, [2] * 3, [2] * 3, prior, dhondt_gen)
        improved, demo = switching_plus(votes, [2] * 3, [2] * 3, prior, dhondt_gen)

        np.testing.assert_array_equal(improved, [[1, 1, 0], [0, 0, 2], [1, 1, 0]])
        np.testing.assert_array_equal(improved.sum(axis=0), normal.sum(axis=0))
        np.testing.assert_array_equal(improved.sum(axis=1), normal.sum(axis=1))
        self.assertEqual(demo['data']['switches'], original_demo['data']['switches'])
        exchanges = demo['data']['exchanges']
        self.assertEqual(len(exchanges), 1)
        self.assertAlmostEqual(exchanges[0]['log_gain'], log(5 / 3))
        self.assertAlmostEqual(
            entropy(votes, improved, dhondt_gen) - entropy(votes, normal, dhondt_gen),
            sum(step['log_gain'] for step in exchanges))
        self.assertIs(ADJUSTMENT_METHODS['switching-plus'], switching_plus)

    def test_exchanges_protect_fixed_seats(self):
        allocation = np.array([[1, 0], [0, 1]])
        protected = np.array([[1, 0], [0, 0]])
        improved, exchanges = improve_by_exchanges(
            [[50, 100], [100, 50]], allocation, protected, dhondt_gen)

        np.testing.assert_array_equal(improved, allocation)
        self.assertEqual(exchanges, [])

    def test_equal_product_is_not_exchanged(self):
        allocation = np.array([[1, 0], [0, 1]])
        improved, exchanges = improve_by_exchanges(
            [[100, 100], [100, 100]], allocation,
            np.zeros((2, 2), dtype=int), dhondt_gen)

        np.testing.assert_array_equal(improved, allocation)
        self.assertEqual(exchanges, [])

    def test_flexible_pool_is_rejected(self):
        self.assertNotIn('switching-plus', FLEXIBLE_ADJUSTMENT_METHODS)
        with self.assertRaisesRegex(ValueError, 'does not support flexible'):
            switching_plus(
                [[100, 50], [50, 100]], [0, 0], [1, 1],
                np.zeros((2, 2), dtype=int), dhondt_gen,
                min_adj_seats=[0, 0], max_adj_seats=[None, None],
                num_adjustment_seats=2)

    def test_election_and_excel_include_exchange_table(self):
        table = load_votes('../data/2-by-2-example.csv')
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        system.update(name='Switching+', adjustment_method='switching-plus')
        handler = ElectionHandler(table, [system], True)
        election = handler.elections[0]

        self.assertEqual(len(election.demo_tables), 3)
        self.assertEqual(election.demo_tables[-1]['sup_header'], 'Improving exchanges')
        for demo in election.demo_tables:
            self.assertEqual(len(demo['headers']), len(demo['format']))
            self.assertTrue(all(len(row) == len(demo['headers']) for row in demo['steps']))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'switching-plus.xlsx'
            handler.to_xlsx(path)
            book = load_workbook(path)
            text = [cell.value for sheet in book for row in sheet for cell in row]
            self.assertIn('Improving exchanges', text)
            book.close()


if __name__ == '__main__':
    unittest.main()
