from copy import deepcopy
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest

import numpy as np

from dictionaries import DIVIDER_RULES
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from noweb import load_votes


class MarginMethodsTest(unittest.TestCase):
    def election(self, method, table, rule='dhondt'):
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        system['adjustment_method'] = method
        system['adj_alloc_divider'] = rule
        return ElectionHandler(deepcopy(table), [system], True)

    def test_standard_example_completes_with_each_divisor(self):
        table = load_votes('../data/2-by-2-example.csv')
        for method in ('max-relative-margin', 'max-absolute-margin'):
            for rule in DIVIDER_RULES:
                with self.subTest(method=method, rule=rule):
                    election = self.election(method, table, rule).elections[0]
                    allocation = np.asarray(election.results['all_const_seats'])
                    np.testing.assert_array_equal(allocation.sum(axis=1), [12, 13])
                    np.testing.assert_array_equal(allocation.sum(axis=0), [13, 12])
                    self.assertTrue((allocation >= election.results['fixed_const_seats']).all())
                    steps = election.demo_tables[0]['steps']
                    self.assertEqual(len(steps), 5)
                    self.assertEqual(steps[-1][3], 'Only party with seats remaining')
                    self.assertEqual(steps[-1][4], '-')

    def test_single_eligible_party_from_start(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['votes'] = [[0, 100], [0, 200]]
        for method in ('max-relative-margin', 'max-absolute-margin'):
            with self.subTest(method=method):
                election = self.election(method, table).elections[0]
                np.testing.assert_array_equal(
                    election.results['all_const_seats'], [[0, 12], [0, 13]])
                self.assertTrue(all(step[4] == '-'
                                    for step in election.demo_tables[0]['steps']))

    def test_undefined_margin_exports_as_dash(self):
        from openpyxl import load_workbook

        table = load_votes('../data/2-by-2-example.csv')
        with TemporaryDirectory() as directory:
            for method in ('max-relative-margin', 'max-absolute-margin'):
                with self.subTest(method=method):
                    handler = self.election(method, table)
                    filename = Path(directory) / f'{method}.xlsx'
                    handler.to_xlsx(filename)
                    workbook = load_workbook(filename)
                    try:
                        cells = [cell for sheet in workbook for row in sheet for cell in row
                                 if cell.value == 'Only party with seats remaining']
                        self.assertTrue(cells)
                        for cell in cells:
                            self.assertEqual(cell.offset(column=1).value, '-')
                    finally:
                        workbook.close()
