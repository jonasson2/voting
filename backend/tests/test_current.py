from contextlib import redirect_stdout
from copy import deepcopy
from io import BytesIO, StringIO
import unittest

import numpy as np

from apportion import apportion1d_general
from dictionaries import DIVIDER_RULES
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from noweb import load_votes
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

    def test_exact_percentage_threshold_qualifies(self):
        allocation, _, _ = apportion1d_general(
            v_votes=[400, 600],
            num_total_seats=10,
            prior_allocations=[],
            rule=DIVIDER_RULES['dhondt'],
            threshold_percent=40,
        )
        self.assertEqual(allocation.tolist(), [4, 6])

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
