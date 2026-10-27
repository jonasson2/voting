"""Report terminology must preserve data, names, and file schemas."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest
from unittest.mock import Mock

from openpyxl import load_workbook
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from excel_util import simulation_to_xlsx, demo_table_to_xlsx
from input_files import load_votes
from sim import run_simulation, write_csv
from simulate import SimulationSettings
from terminology import label, label_table, report_terminology, term


class TerminologyTest(unittest.TestCase):
    def test_demo_explanations_translate_but_names_do_not(self):
        worksheet = Mock()
        table = {'headers': ['Constituency', 'Party', 'Criteria'],
                 'steps': [['Const. North', 'Adj. Party', 'No const. seat']],
                 'format': ['l', 'l', 'l'], 'sup_header': None}
        report_terminology(demo_table_to_xlsx)(
            worksheet, 0, 0, {'step_h': None, 'l': None}, table,
            terminology={'constituency': 'district', 'adjustment_seat': 'levelling'})
        worksheet.write.assert_any_call(2, 0, 'Const. North', None)
        worksheet.write.assert_any_call(2, 1, 'Adj. Party', None)
        worksheet.write.assert_any_call(2, 2, 'No dist. seat', None)

    def test_abbreviations(self):
        for choice, short in [('constituency', 'const.'), ('district', 'dist.'),
                              ('electorate', 'elect.')]:
            self.assertEqual(report_terminology(label)(
                'Const. vote score; all as const. seats; CONST.',
                terminology={'constituency': choice}),
                f'{short.capitalize()} vote score; all as {short} seats; {short.upper()}')

    def test_forms_and_request_isolation(self):
        self.assertEqual(term('constituency', plural=True), 'constituencies')
        barrier = Barrier(2)

        @report_terminology
        def render():
            barrier.wait(timeout=5)
            return label('Constituency votes in all constituencies; CONSTITUENCY')

        with ThreadPoolExecutor(2) as executor:
            futures = [executor.submit(render, terminology={'constituency': choice})
                       for choice in ('district', 'electorate')]
            self.assertEqual([future.result() for future in futures], [
                'District votes in all districts; DISTRICT',
                'Electorate votes in all electorates; ELECTORATE'])
        self.assertEqual(label('Constituency'), 'Constituency')
        self.assertEqual(report_terminology(label)('A constituency and a constituency',
                         terminology={'constituency': 'electorate'}),
                         'An electorate and an electorate')
        with self.assertRaises(ValueError):
            render(terminology={'constituency': 'unknown'})

    def test_label_table_preserves_comparison_names(self):
        table = {'group_ids': ['cmpList', 'const'], 'system_names': ['Constituency system'],
                 'group_titles': {'const': 'Constituency measures'},
                 'cmpList': [{'measure': 'cmp_Constituency system_const',
                              'rowtitle': 'Constituency system', 'avg': [1]}],
                 'const': [{'measure': 'disparity', 'rowtitle': 'Constituency disparity'}]}
        original = deepcopy(table)
        result = report_terminology(label_table)(table, terminology={'constituency': 'district'})
        self.assertEqual(table, original)
        self.assertEqual(result['cmpList'], table['cmpList'])
        self.assertEqual(result['system_names'], table['system_names'])
        self.assertEqual(result['const'][0]['rowtitle'], 'District disparity')

    def test_reports_preserve_numbers_names_and_result_data(self):
        votes = load_votes('../data/2-by-2-example.csv')
        votes['name'] = 'Constituency adjustment seats input'
        votes['constituencies'][0]['name'] = 'Northern Constituency'
        votes['parties'][0] = 'Constituency Party'
        system = ElectionSystem()
        system.copy_info_from_votes(votes)
        system['name'] = 'Constituency adjustment system'
        settings = dict(SimulationSettings(), random_seed=123, simulation_count=2,
                        cpu_count=1, sensitivity=False, single_list_sensitivity=False,
                        show_additional=True, show_scalings=True, show_single_seat=True)
        result = run_simulation(votes, [system], settings)
        before = deepcopy(result.get_result_web(False))
        handler = ElectionHandler(votes, [system], use_thresholds=True)
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            numbers = {}
            for choice, seat_term in [('constituency', 'adjustment'), ('district', 'adjustment'),
                                      ('electorate', 'adjustment'),
                                      *(("electorate", term) for term in
                                        ('compensatory', 'equalisation', 'levelling', 'top-up'))]:
                preference = {'constituency': choice, 'adjustment_seat': seat_term}
                path = directory / f'{choice}.csv'
                write_csv(path, result, terminology=preference)
                with path.open() as file:
                    rows = list(csv.reader(file))
                plural = 'constituencies' if choice == 'constituency' else choice + 's'
                self.assertIn([f'Number of {plural}', '2'], rows)
                self.assertIn('Constituency adjustment system', path.read_text())
                abbreviation = {'adjustment': 'adj.', 'compensatory': 'comp.',
                                'equalisation': 'equal.', 'levelling': 'lev.', 'top-up': 'top-up'}[seat_term]
                self.assertIn([f'Total number of {abbreviation} seats',
                               str(sum(c['num_adj_seats'] for c in votes['constituencies']))], rows)
                self.assertIn('Constituency adjustment seats input', path.read_text())
                self.assertIn(choice.capitalize() + ' disparity', path.read_text())
                for kind in ('simulation', 'election'):
                    path = directory / f'{choice}-{kind}.xlsx'
                    if kind == 'simulation':
                        simulation_to_xlsx(result.get_result_web(False), path, terminology=preference)
                    else:
                        handler.to_xlsx(path, terminology=preference)
                    book = load_workbook(path)
                    numeric = [(sheet.title, cell.coordinate, cell.value)
                               for sheet in book for row in sheet for cell in row
                               if isinstance(cell.value, (int, float))]
                    if choice == 'constituency': numbers[kind] = numeric
                    else: self.assertEqual(numbers[kind], numeric)
                    strings = [cell.value for sheet in book for row in sheet for cell in row
                               if isinstance(cell.value, str)]
                    for name in ('Northern Constituency', 'Constituency Party', 'Constituency adjustment system'):
                        self.assertIn(name, strings)
                    seat_label = 'equalization' if seat_term == 'equalisation' else seat_term
                    self.assertIn(seat_label.capitalize() + ' seats', strings)
                    if seat_term != 'adjustment':
                        self.assertNotIn('Adjustment seats', strings)
                    if kind == 'simulation':
                        self.assertIn(choice.capitalize() + ' disparity', strings)
                        comments = [cell.comment.text for sheet in book for row in sheet for cell in row if cell.comment]
                        if choice != 'constituency':
                            self.assertFalse(any('constituency' in text.lower() for text in comments))
                    else:
                        self.assertIn(choice.capitalize(), strings)
                    book.close()
        self.assertEqual(result.get_result_web(False), before)


class AdjustmentTerminologyTest(unittest.TestCase):
    def test_forms_and_cli_choices(self):
        from argparse import ArgumentParser
        from terminology import add_terminology_option, terminology_from_args
        parser = ArgumentParser()
        add_terminology_option(parser)
        for seat_term, short in [('adjustment', 'adj.'), ('compensatory', 'comp.'),
                                 ('equalisation', 'equal.'), ('levelling', 'lev.'),
                                 ('top-up', 'top-up')]:
            args = parser.parse_args(['--adjustment-seat-term', seat_term,
                                      '--constituency-term', 'electorate'])
            preferences = terminology_from_args(args)
            render = report_terminology(label)
            seat_label = 'equalization' if seat_term == 'equalisation' else seat_term
            self.assertEqual(render('Adjustment seats in all constituencies', terminology=preferences),
                             seat_label.capitalize() + ' seats in all electorates')
            self.assertEqual(render('adjustment-seat bounds; fixed + adjustment seats; # Min adj.',
                                    terminology=preferences),
                             f'{seat_label}-seat bounds; fixed + {seat_label} seats; # Min {short}')
            article = 'an' if seat_term in ('adjustment', 'equalisation') else 'a'
            self.assertEqual(render('an adjustment seat', terminology=preferences),
                             f'{article} {seat_label} seat')
            self.assertEqual(render('adjustment_method num_adj_seats adjacent', terminology=preferences),
                             'adjustment_method num_adj_seats adjacent')
