from contextlib import redirect_stdout
from copy import deepcopy
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from apportion import apportion1d_general, threshold_drop
from dictionaries import DIVIDER_RULES
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from input_util import check_vote_table
from noweb import load_votes, votes_to_excel
from web import app


class CurrentApplicationTest(unittest.TestCase):
    def make_system(self, table, method, threshold=0):
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        system['adjustment_method'] = method
        system['adjustment_threshold'] = threshold
        return system

    def test_csv_upload_uses_uploaded_stream(self):
        app.config.update(TESTING=True)
        client = app.test_client()
        upload = BytesIO(b'Example,fixed,adj,A,B\nI,1,0,10,20\n')
        data = {'file': (upload, 'votes.csv')}
        response = client.post('/api/votes/upload/', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['votes'], [[10, 20]])

    def test_csv_upload_reads_pruned_votes(self):
        app.config.update(TESTING=True)
        client = app.test_client()
        upload = BytesIO(
            b'Example,fixed,adj,A,B,Pruned\n'
            b'I,1,0,10,20,3\n'
        )
        data = {'file': (upload, 'votes.csv')}
        response = client.post('/api/votes/upload/', data=data)
        self.assertEqual(response.status_code, 200)
        vote_table = response.get_json()
        self.assertEqual(vote_table['parties'], ['A', 'B'])
        self.assertEqual(vote_table['votes'], [[10, 20]])
        self.assertEqual(vote_table['pruned'], [3])

    def test_excel_round_trip_preserves_pruned_votes(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['pruned'] = [3, 4]
        table['party_vote_info'] = {
            'name': 'National',
            'num_fixed_seats': 0,
            'num_adj_seats': 0,
            'votes': [12, 21],
            'specified': True,
            'total': 37,
            'pruned': 4,
        }
        with TemporaryDirectory() as directory:
            filename = Path(directory) / 'votes.xlsx'
            votes_to_excel(table, filename)
            loaded = load_votes(filename)
        self.assertEqual(loaded['pruned'], [3, 4])
        self.assertEqual(loaded['party_vote_info']['pruned'], 4)

    def test_exact_percentage_threshold_qualifies(self):
        allocation, _, _ = apportion1d_general(
            v_votes=[400, 600],
            num_total_seats=10,
            prior_allocations=[],
            rule=DIVIDER_RULES['dhondt'],
            threshold_percent=40,
        )
        self.assertEqual(allocation.tolist(), [4, 6])

    def test_percentage_threshold_can_use_complete_vote_total(self):
        threshold = [0, 4, 0, None]
        self.assertEqual(threshold_drop([39, 936], threshold), [39, 936])
        self.assertEqual(
            threshold_drop([39, 936], threshold, threshold_total=1000),
            [0, 936],
        )

    def test_constituency_threshold_includes_pruned_votes(self):
        table = {
            'name': 'Threshold example',
            'parties': ['A', 'B'],
            'votes': [[39, 936]],
            'pruned': [25],
            'constituencies': [{
                'name': 'I',
                'num_fixed_seats': 100,
                'num_adj_seats': 0,
            }],
            'party_vote_info': {
                'name': '-',
                'num_fixed_seats': 0,
                'num_adj_seats': 0,
                'votes': [],
                'specified': False,
                'total': 0,
                'pruned': 0,
            },
        }
        system = self.make_system(table, 'max-const-seat-share', threshold=0)
        system['constituency_threshold'] = 4
        handler = ElectionHandler(table, [system], use_thresholds=True)
        allocation = handler.elections[0].results['fixed_const_seats'][0]
        self.assertEqual(allocation, [0, 100])

    def test_national_threshold_totals_include_matching_pruned_votes(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['pruned'] = [100, 200]
        table['party_vote_info'] = {
            'name': 'National',
            'num_fixed_seats': 0,
            'num_adj_seats': 0,
            'votes': [4000, 4000],
            'specified': True,
            'total': 8400,
            'pruned': 400,
        }
        expected_totals = {
            'totals': 8000,
            'party_vote_info': 8400,
            'average': 8200,
        }
        for basis, expected in expected_totals.items():
            with self.subTest(basis=basis):
                system = self.make_system(table, 'max-const-seat-share')
                system['seat_spec_options']['party'] = basis
                handler = ElectionHandler(
                    table, [system], use_thresholds=True)
                self.assertEqual(
                    handler.elections[0].nat_threshold_total, expected)

    def test_national_threshold_excludes_party_below_complete_vote_share(self):
        table = {
            'name': 'National threshold example',
            'parties': ['A', 'B'],
            'votes': [[500, 500]],
            'pruned': [0],
            'constituencies': [{
                'name': 'I',
                'num_fixed_seats': 0,
                'num_adj_seats': 100,
            }],
            'party_vote_info': {
                'name': 'National',
                'num_fixed_seats': 0,
                'num_adj_seats': 0,
                'votes': [39, 936],
                'specified': True,
                'total': 1000,
                'pruned': 25,
            },
        }
        system = self.make_system(table, 'max-const-seat-share', threshold=4)
        system['seat_spec_options']['party'] = 'party_vote_info'
        handler = ElectionHandler(table, [system], use_thresholds=True)
        self.assertEqual(
            handler.elections[0].desired_col_sums.tolist(), [0, 100])

    def test_simulated_votes_keep_recorded_pruned_threshold_total(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['pruned'] = [100, 200]
        system = self.make_system(table, 'max-const-seat-share')
        handler = ElectionHandler(table, [system], use_thresholds=True)
        generated = [[1000, 2000], [3000, 4000]]
        handler.run_elections(True, votes=generated)
        self.assertEqual(
            handler.elections[0].const_threshold_totals.tolist(),
            [3100, 7200],
        )

    def test_old_vote_tables_default_to_no_pruned_votes(self):
        table = load_votes('../data/2-by-2-example.csv')
        table.pop('pruned')
        table['party_vote_info'].pop('pruned')
        checked = check_vote_table(table)
        self.assertEqual(checked['pruned'], [0, 0])
        self.assertEqual(checked['party_vote_info']['pruned'], 0)

    def test_average_national_vote_basis(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['party_vote_info'] = {
            'name': 'National',
            'num_fixed_seats': 0,
            'num_adj_seats': 0,
            'votes': [4000, 4000],
            'specified': True,
            'total': 8000,
        }
        system = self.make_system(table, 'max-const-seat-share')
        system['seat_spec_options']['party'] = 'average'
        handler = ElectionHandler(table, [system], use_thresholds=True)
        self.assertEqual(handler.elections[0].nat_votes.tolist(), [4000, 3850])

    def test_representative_methods_preserve_margins(self):
        cases = [
            ('../data/iceland-2021.csv', 'icelandic-law', 5),
            ('../data/norway_2025.csv', 'norwegian-law', 4),
            ('../data/iceland-2021.csv', 'max-const-seat-share', 0),
            ('../data/iceland-2021.csv', 'switching', 0),
            ('../data/iceland-2021.csv', 'alternating-scaling', 0),
        ]
        for filename, method, threshold in cases:
            with self.subTest(method=method):
                table = load_votes(filename)
                system = self.make_system(table, method, threshold)
                with redirect_stdout(StringIO()):
                    handler = ElectionHandler(table, [deepcopy(system)], True)
                election = handler.elections[0]
                allocation = np.asarray(election.results['all_const_seats'])
                row_totals = [
                    constituency['num_fixed_seats'] + constituency['num_adj_seats']
                    for constituency in election.system['constituencies']
                ]
                self.assertEqual(allocation.sum(axis=1).tolist(), row_totals)
                self.assertEqual(
                    allocation.sum(axis=0).tolist(),
                    election.desired_col_sums.tolist(),
                )
