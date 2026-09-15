from contextlib import redirect_stdout
from copy import deepcopy
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from apportion import apportion1d_general, threshold_drop
from dictionaries import (ADJUSTMENT_METHODS, DIVIDER_RULES,
                          ELECTION_LAW_PRESETS, QUOTA_RULES)
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from noweb import load_json, load_votes, votes_to_excel
import noweb
from par_util import parallel_dir
from simulate import Simulation, SimulationSettings
from methods.max_const_votes import max_const_votes
from methods.switching_se import switching as swedish_switching
from vote_table import check_vote_table
import web
from web import app


class CurrentApplicationTest(unittest.TestCase):
    def make_system(self, table, method, threshold=0):
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        system['adjustment_method'] = method
        system['adjustment_threshold'] = threshold
        return system

    def make_swedish_system(self, table, divider='nordic-1.2'):
        system = self.make_system(table, 'max-const-votes', threshold=4)
        system['primary_divider'] = divider
        system['adj_determine_divider'] = divider
        system['adjustment_preparation_method'] = 'switching_se'
        system['adj_preparation_divider'] = divider
        system['adj_alloc_divider'] = 'sainte-lague'
        system['constituency_threshold'] = 12
        system['fixed_seat_eligibility'] = 'national-or-constituency'
        return system

    def test_wsgi_import_initializes_simulation_state(self):
        self.assertIsInstance(noweb.SIMULATIONS, dict)

    def test_default_web_ports(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(
                    web.os, 'uname',
                    return_value=SimpleNamespace(nodename='pluto.cs.hi.is')):
                self.assertEqual(web.default_port(), '5000')
            with patch.object(
                    web.os, 'uname',
                    return_value=SimpleNamespace(nodename='workstation')):
                self.assertEqual(web.default_port(), '5001')
        with patch.dict(os.environ, {'FLASK_RUN_PORT': '5050'}):
            self.assertEqual(web.default_port(), '5050')

    def test_parallel_files_can_use_service_state_directory(self):
        with TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"VOTING_STATE_DIR": directory}):
                self.assertEqual(parallel_dir(), Path(directory) / "pardir")

    def test_single_cpu_simulation_runs_in_background_thread(self):
        class FakeThread:
            def __init__(self, target, args):
                self.target = target
                self.args = args
                self.started = False

            def start(self):
                self.started = True

        noweb.create_SIMULATIONS()
        with patch.object(noweb, 'Thread', FakeThread), \
             patch.object(noweb, 'Simulation', return_value=object()), \
             patch.object(noweb.par_util, 'get_id', return_value='single-cpu'):
            simid = noweb.new_simulation(
                votes={}, systems=[],
                sim_settings={'cpu_count': 1},
            )

        simulation = noweb.SIMULATIONS[simid]
        self.assertEqual(simulation['kind'], 'threaded')
        self.assertTrue(simulation['thread'].started)

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

    def test_csv_upload_reads_party_names(self):
        app.config.update(TESTING=True)
        client = app.test_client()
        upload = BytesIO(
            b'Example,fixed,adj,A,B\n'
            b'Party names,,,Alpha Party,Beta Party\n'
            b'I,1,0,10,20\n'
        )
        response = client.post('/api/votes/upload/',
                               data={'file': (upload, 'votes.csv')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['party_names'],
                         ['Alpha Party', 'Beta Party'])

    def test_csv_upload_reads_adjustment_seat_maxima(self):
        app.config.update(TESTING=True)
        client = app.test_client()
        upload = BytesIO(
            b'Example,fixed,min_adj,max_adj,A,B\n'
            b'Max adj seats,,,5,,\n'
            b'I,1,2,4,10,20\n'
            b'II,1,1,-,30,40\n'
        )
        response = client.post('/api/votes/upload/',
                               data={'file': (upload, 'votes.csv')})
        self.assertEqual(response.status_code, 200)
        vote_table = response.get_json()
        self.assertEqual(vote_table['max_total_adj_seats'], 5)
        self.assertEqual(
            [constituency['max_adj_seats']
             for constituency in vote_table['constituencies']],
            [4, None],
        )

    def test_csv_upload_rejects_blank_adjustment_seat_maximum(self):
        app.config.update(TESTING=True)
        upload = BytesIO(
            b'Example,fixed,min_adj,max_adj,A\n'
            b'Max adj seats,,,1,\n'
            b'I,1,0,,10\n'
        )
        response = app.test_client().post(
            '/api/votes/upload/', data={'file': (upload, 'votes.csv')})
        self.assertIn(
            'must be a non-negative integer or - for unlimited',
            response.get_json()['error'],
        )

    def test_csv_upload_reads_national_votes_after_blank_row(self):
        app.config.update(TESTING=True)
        client = app.test_client()
        upload = BytesIO(
            b'Example,fixed,adj,A,B\n'
            b'I,1,0,10,20\n'
            b'\n'
            b'National,0,1,30,40\n'
        )
        response = client.post('/api/votes/upload/',
                               data={'file': (upload, 'votes.csv')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()['party_vote_info']['votes'], [30, 40])

    def test_csv_upload_normalizes_blank_national_votes_to_zero(self):
        app.config.update(TESTING=True)
        client = app.test_client()
        upload = BytesIO(
            b'Example,fixed,adj,A,B\n'
            b'I,1,0,10,20\n'
            b'\n'
            b'National,0,1,,\n'
        )
        response = client.post('/api/votes/upload/',
                               data={'file': (upload, 'votes.csv')})
        self.assertEqual(response.status_code, 200)
        info = response.get_json()['party_vote_info']
        self.assertEqual(info['votes'], [0, 0])
        self.assertEqual(info['total'], 0)

    def test_short_vote_file_returns_a_format_error(self):
        app.config.update(TESTING=True)
        client = app.test_client()
        upload = BytesIO(b'Example,fixed\nI,1\n')
        response = client.post('/api/votes/upload/',
                               data={'file': (upload, 'votes.csv')})
        self.assertIn('seat columns', response.get_json()['error'])

    def test_vote_table_validation_rejects_invalid_numbers(self):
        table = load_votes('../data/2-by-2-example.csv')
        cases = [
            ('fractional votes', ('votes', 1.5)),
            ('non-finite votes', ('votes', float('nan'))),
            ('negative seats', ('seats', -1)),
        ]
        for description, (kind, value) in cases:
            with self.subTest(description):
                invalid = deepcopy(table)
                if kind == 'votes':
                    invalid['votes'][0][0] = value
                else:
                    invalid['constituencies'][0]['num_fixed_seats'] = value
                with self.assertRaises((TypeError, ValueError)):
                    check_vote_table(invalid)

    def test_specified_national_vote_name_must_be_nonblank(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['party_vote_info'] = {
            'name': ' ',
            'num_fixed_seats': 0,
            'num_adj_seats': 0,
            'votes': [10, 20],
            'specified': True,
            'pruned': 0,
        }
        with self.assertRaisesRegex(ValueError, 'non-blank'):
            check_vote_table(table)

    def test_vote_table_api_validates_edited_tables(self):
        app.config.update(TESTING=True)
        client = app.test_client()
        table = load_votes('../data/2-by-2-example.csv')
        table['constituencies'][0]['num_fixed_seats'] = -1
        response = client.post('/api/votes/save/', json={'vote_table': table})
        self.assertIn('may not be negative', response.get_json()['error'])

        table = load_votes('../data/2-by-2-example.csv')
        table['votes'][0][0] = -1
        response = client.post('/api/votes/save/', json={'vote_table': table})
        self.assertIn('Votes may not be negative', response.get_json()['error'])

        table = load_votes('../data/2-by-2-example.csv')
        table['max_total_adj_seats'] = 5
        table['constituencies'][0]['max_adj_seats'] = 1
        table['constituencies'][1]['max_adj_seats'] = None
        response = client.post('/api/votes/save/', json={'vote_table': table})
        self.assertIn('Maximum adjustment seats may not be below the minimum',
                      response.get_json()['error'])

    def test_vote_table_api_download_can_be_uploaded(self):
        app.config.update(TESTING=True)
        client = app.test_client()
        table = load_votes('../data/iceland-2021.csv')

        download = client.post('/api/votes/save/', json={'vote_table': table})
        self.assertEqual(download.status_code, 200)
        upload = client.post(
            '/api/votes/upload/',
            data={'file': (BytesIO(download.data), 'votes.xlsx')},
        )

        self.assertEqual(upload.status_code, 200)
        self.assertNotIn('error', upload.get_json())
        self.assertEqual(upload.get_json()['votes'], table['votes'])

    def test_swedish_vote_table_uses_adjustment_seat_bounds(self):
        table = load_votes('../data/sweden_2022.csv')
        self.assertEqual(table['max_total_adj_seats'], 39)
        self.assertTrue(all(
            constituency['num_adj_seats'] == 0
            and constituency['max_adj_seats'] is None
            for constituency in table['constituencies']
        ))

    def test_swedish_elections_are_available_as_presets(self):
        app.config.update(TESTING=True)
        client = app.test_client()
        presets = client.get('/api/presets/').get_json()
        swedish = [preset for preset in presets
                   if preset['Country'] == 'Sweden']
        self.assertEqual(
            [preset['Year'] for preset in swedish],
            ['2014', '2018', '2022'],
        )
        for preset in swedish:
            response = client.post(
                '/api/presets/load/',
                json={'election_id': presets.index(preset)},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.get_json()['name'],
                f"Sweden-Riksdagen-{preset['Year']}",
            )

    def test_election_law_presets_contain_rules_but_no_seat_counts(self):
        presets = {
            preset['value']: preset['settings']
            for preset in ELECTION_LAW_PRESETS if preset['settings']
        }
        self.assertEqual(
            list(presets),
            ['denmark', 'finland', 'iceland', 'norway', 'sweden-2014', 'sweden-2018'],
        )
        self.assertEqual(
            [preset['text'] for preset in ELECTION_LAW_PRESETS[1:]],
            [
                'Denmark (2007–present)',
                'Finland (1907–present)',
                'Iceland (2003–present)',
                'Norway (2005–present)',
                'Sweden (1988–2014)',
                'Sweden (2018–present)',
            ],
        )
        self.assertEqual(
            (presets['finland']['primary_divider'],
             presets['finland']['constituency_threshold'],
             presets['finland']['adjustment_method'],
             presets['finland']['constituency_seat_specification']),
            ('dhondt', 0, 'adjustment-as-fixed', 'refer'),
        )
        self.assertEqual(
            (presets['iceland']['adjustment_method'],
             presets['iceland']['adjustment_threshold'],
             presets['iceland']['primary_divider']),
            ('icelandic-law', 5, 'dhondt'),
        )
        self.assertEqual(
            (presets['norway']['adjustment_method'],
             presets['norway']['adjustment_threshold'],
             presets['norway']['primary_divider'],
             presets['norway']['adj_alloc_divider']),
            ('norwegian-law', 4, 'nordic-1.4', 'sainte-lague'),
        )
        self.assertEqual(
            (presets['sweden-2014']['constituency_threshold'],
             presets['sweden-2014']['fixed_seat_eligibility'],
             presets['sweden-2014']['adjustment_preparation_method'],
             presets['sweden-2014']['adj_preparation_divider'],
             presets['sweden-2014']['adjustment_method'],
             presets['sweden-2014']['constituency_seat_specification']),
            (12, 'national-or-constituency', 'none', 'nordic-1.4',
             'max-const-votes', 'refer'),
        )
        self.assertEqual(
            (presets['sweden-2018']['constituency_threshold'],
             presets['sweden-2018']['fixed_seat_eligibility'],
             presets['sweden-2018']['adjustment_preparation_method'],
             presets['sweden-2018']['adj_preparation_divider'],
             presets['sweden-2018']['adjustment_method'],
             presets['sweden-2018']['constituency_seat_specification']),
            (12, 'national-or-constituency', 'switching_se', 'nordic-1.2',
             'max-const-votes', 'refer'),
        )
        forbidden = {
            'constituencies', 'num_fixed_seats', 'num_adj_seats',
            'max_adj_seats', 'max_total_adj_seats',
            'additional_adjustment_method', 'additional_adj_alloc_divider',
        }
        for settings in presets.values():
            self.assertTrue(forbidden.isdisjoint(settings))

        client = app.test_client()
        response = client.post('/api/capabilities/', json={})
        self.assertEqual(
            response.get_json()['capabilities']['election_law_presets'],
            ELECTION_LAW_PRESETS,
        )

    def test_swedish_divisor_starts_at_1_2(self):
        generator = DIVIDER_RULES['nordic-1.2']()
        self.assertEqual([next(generator) for _ in range(4)], [1.2, 3, 5, 7])

    def test_finnish_2015_matches_official_party_seat_totals(self):
        table = load_votes('../data/finland_2015.csv')
        settings = next(
            preset['settings'] for preset in ELECTION_LAW_PRESETS
            if preset['value'] == 'finland'
        )
        system = self.make_system(table, settings['adjustment_method'])
        system.update(deepcopy(settings))
        election = ElectionHandler(table, [system], True).elections[0]

        self.assertEqual(
            dict(zip(table['parties'], election.results['all_const_total'])),
            {
                'CENT': 49, 'SAML': 37, 'SAF': 38, 'SDP': 34,
                'GRÖNA': 15, 'VÄNST': 12, 'SFP': 9, 'KD': 5,
                'Piratp': 0, 'IP': 0, 'FKP': 0, 'Åland': 1,
            },
        )
        self.assertEqual(sum(election.results['all_const_total']), 200)

    def test_recent_finnish_elections_are_available_as_presets(self):
        app.config.update(TESTING=True)
        client = app.test_client()
        presets = client.get('/api/presets/').get_json()
        finnish = [preset for preset in presets
                   if preset['Country'] == 'Finland']
        self.assertEqual(
            [preset['Year'] for preset in finnish],
            ['2015', '2019', '2023'],
        )
        for preset in finnish:
            response = client.post(
                '/api/presets/load/',
                json={'election_id': presets.index(preset)},
            )
            self.assertEqual(response.status_code, 200)

    def test_recent_finnish_elections_match_official_party_seat_totals(self):
        expected = {
            '2019': {
                'SDP': 40, 'PS': 39, 'KOK': 38, 'KESK': 31,
                'VIHR': 20, 'VAS': 16, 'RKP': 9, 'KD': 5,
                'LIIKE': 1, '05-FÅ': 1,
            },
            '2023': {
                'KOK': 48, 'PS': 46, 'SDP': 43, 'KESK': 23,
                'VIHR': 13, 'VAS': 11, 'RKP': 9, 'KD': 5,
                'LIIKE': 1, '05-FÅ': 1,
            },
        }
        settings = next(
            preset['settings'] for preset in ELECTION_LAW_PRESETS
            if preset['value'] == 'finland'
        )

        for year, official in expected.items():
            with self.subTest(year=year):
                table = load_votes(f'../data/finland_{year}.csv')
                system = self.make_system(table, settings['adjustment_method'])
                system.update(deepcopy(settings))
                election = ElectionHandler(table, [system], True).elections[0]
                totals = dict(zip(
                    table['parties'],
                    election.results['all_const_total'],
                ))
                self.assertEqual(
                    {party: seats for party, seats in totals.items() if seats},
                    official,
                )
                self.assertEqual(sum(totals.values()), 200)

    def test_swedish_2018_matches_official_seat_margins(self):
        table = load_votes('../data/sweden_2018.csv')
        election = ElectionHandler(
            table, [self.make_swedish_system(table)], True).elections[0]
        allocation = np.asarray(election.results['all_const_seats'])
        expected_additional = [
            4, 3, 2, 1, 2, 2, 0, 0, 0, 0, 2, 2, 1, 1, 3,
            2, 2, 1, 1, 2, 2, 3, 1, 1, 0, 0, 1, 0, 0,
        ]
        expected_party_totals = {
            'M': 70, 'C': 31, 'L': 20, 'KD': 22,
            'S': 100, 'V': 28, 'MP': 16, 'SD': 62,
        }
        self.assertEqual(
            (allocation.sum(axis=1) - election.desired_row_sums).tolist(),
            expected_additional,
        )
        self.assertEqual(
            {party: int(seats) for party, seats in
             zip(table['parties'], allocation.sum(axis=0)) if seats},
            expected_party_totals,
        )
        self.assertEqual(
            election.demo_tables[0]['steps'][0][2],
            'No switching required',
        )

    def test_swedish_2014_matches_official_party_totals_without_switching(self):
        table = load_votes('../data/sweden_2014.csv')
        settings = next(
            preset['settings'] for preset in ELECTION_LAW_PRESETS
            if preset['value'] == 'sweden-2014'
        )
        system = self.make_system(table, settings['adjustment_method'])
        system.update(deepcopy(settings))
        election = ElectionHandler(table, [system], True).elections[0]
        allocation = np.asarray(election.results['all_const_seats'])
        self.assertEqual(
            {party: int(seats) for party, seats in
             zip(table['parties'], allocation.sum(axis=0)) if seats},
            {
                'M': 84, 'C': 22, 'L': 19, 'KD': 16,
                'S': 113, 'V': 21, 'MP': 25, 'SD': 49,
            },
        )
        self.assertIsNone(election.preparation_stepbystep)

    def test_swedish_2022_matches_official_seat_margins(self):
        table = load_votes('../data/sweden_2022.csv')
        election = ElectionHandler(
            table, [self.make_swedish_system(table)], True).elections[0]
        allocation = np.asarray(election.results['all_const_seats'])
        expected_additional = [
            5, 3, 1, 2, 3, 2, 0, 0, 0, 0, 1, 1, 2, 0, 2,
            1, 3, 0, 1, 1, 2, 3, 0, 2, 2, 1, 0, 1, 0,
        ]
        expected_party_totals = {
            'M': 68, 'C': 24, 'L': 16, 'KD': 19,
            'S': 107, 'V': 24, 'MP': 18, 'SD': 73,
        }
        self.assertEqual(
            (allocation.sum(axis=1) - election.desired_row_sums).tolist(),
            expected_additional,
        )
        self.assertEqual(
            {party: int(seats) for party, seats in
            zip(table['parties'], allocation.sum(axis=0)) if seats},
            expected_party_totals,
        )
        self.assertEqual(len(election.demo_tables), 2)
        self.assertEqual(
            election.demo_tables[0]['headers'],
            [
                'Step', 'Constituency', 'From', 'To',
                'Returned quotient', 'Recipient quotient',
            ],
        )
        self.assertEqual(
            election.demo_tables[0]['steps'][0][2],
            'No switching required',
        )
        self.assertEqual(len(election.demo_tables[1]['steps']), 39)
        display = election.get_result_web()['display_results']
        self.assertEqual(
            display[-1][table['parties'].index('M')],
            '68 (+0+1)',
        )
        self.assertEqual(display[-1][-1], '349 (+0+39)')
        unchanged = np.argwhere(
            (np.asarray(election.results['all_const_seats']) > 0)
            & (election.switching_seat_changes == 0)
            & (election.adjustment_seat_allocations == 0)
        )[0]
        c, p = map(int, unchanged)
        self.assertEqual(
            display[c][p], str(election.results['all_const_seats'][c][p]))

    def test_swedish_system_runs_through_simulation_measures(self):
        table = load_votes('../data/sweden_2022.csv')
        settings = SimulationSettings()
        settings['simulation_count'] = 1
        settings['cpu_count'] = 1
        with redirect_stdout(StringIO()):
            simulation = Simulation(
                settings, [self.make_swedish_system(table)], table)
            simulation.run_and_collect_measures(table['votes'], None)
        self.assertEqual(
            sum(simulation.election_handler.elections[0]
                .results['all_const_total']),
            349,
        )

    def test_swedish_switching_returns_an_overhang(self):
        allocation, steps = swedish_switching(
            [[1, 1], [24, 1]],
            [3, 3],
            [3, 3],
            np.array([[1, 2], [3, 0]], dtype=int),
            DIVIDER_RULES['nordic-1.2'],
            nat_votes=np.array([25, 2]),
            total_seats=6,
        )
        np.testing.assert_array_equal(allocation, [[0, 3], [3, 0]])
        np.testing.assert_array_equal(steps['party_totals'], [3, 3])
        self.assertEqual(len(steps['data']['switches']), 1)

    def test_max_const_votes_respects_constituency_capacity(self):
        allocation, _ = max_const_votes(
            [[100, 10], [90, 9]],
            [1, 3],
            [2, 2],
            np.array([[1, 0], [1, 0]]),
            DIVIDER_RULES['sainte-lague'],
            num_adjustment_seats=2,
            min_adj_seats=[0, 2],
            max_adj_seats=[0, 2],
        )
        np.testing.assert_array_equal(allocation, [[1, 0], [1, 2]])

    def test_max_const_votes_respects_constituency_minimums(self):
        allocation, _ = max_const_votes(
            [[1, 1], [100, 100]],
            [2, 0],
            [2, 2],
            np.zeros((2, 2), dtype=int),
            DIVIDER_RULES['sainte-lague'],
            num_adjustment_seats=4,
            min_adj_seats=[2, 0],
            max_adj_seats=[None, None],
        )
        np.testing.assert_array_equal(allocation.sum(axis=1), [2, 2])
        np.testing.assert_array_equal(allocation.sum(axis=0), [2, 2])

    def test_max_const_votes_handles_flexible_adjustment_seat_bounds(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['constituencies'][0]['max_adj_seats'] = 3
        table['constituencies'][1]['max_adj_seats'] = 4
        table['max_total_adj_seats'] = 7
        system = self.make_system(table, 'max-const-votes')

        election = ElectionHandler(table, [system], True).elections[0]
        adjustment = (
            np.asarray(election.results['all_const_seats'])
            - np.asarray(election.results['fixed_const_seats']))

        np.testing.assert_array_equal(adjustment.sum(axis=1), [3, 4])
        self.assertEqual(int(adjustment.sum()), 7)

    def test_ordinary_method_rejects_flexible_adjustment_seat_bounds(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['constituencies'][0]['max_adj_seats'] = 3
        table['constituencies'][1]['max_adj_seats'] = None
        table['max_total_adj_seats'] = 6
        for method in ADJUSTMENT_METHODS:
            if method == 'max-const-votes':
                continue
            with self.subTest(method=method):
                system = self.make_system(table, method)
                with self.assertRaisesRegex(
                        ValueError, 'does not support constituency ranges'):
                    ElectionHandler(table, [system], True)

    def test_ordinary_method_accepts_explicit_exact_adjustment_seats(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['constituencies'][0]['max_adj_seats'] = 2
        table['constituencies'][1]['max_adj_seats'] = 3
        table['max_total_adj_seats'] = 5
        system = self.make_system(table, 'max-const-seat-share')

        election = ElectionHandler(table, [system], True).elections[0]

        np.testing.assert_array_equal(election.final_row_sums, [12, 13])

    def test_generated_party_names_are_included(self):
        cases = [
            ('../data/norway_2017.csv', 'AP', 'Arbeiderpartiet'),
            ('../data/norway_2021.csv', 'AP', 'Arbeiderpartiet'),
            ('../data/norway_2025.csv', 'AP', 'Arbeiderpartiet'),
            ('../data/sweden_2018.csv', 'M', 'Moderaterna'),
        ]
        for filename, abbreviation, name in cases:
            with self.subTest(filename=filename):
                table = load_votes(filename)
                party_index = table['parties'].index(abbreviation)
                self.assertEqual(table['party_names'][party_index], name)

    def test_blank_party_names_are_omitted(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['party_names'] = ['', '  ']
        self.assertNotIn('party_names', check_vote_table(table))

    def test_party_names_must_match_the_party_list(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['party_names'] = ['Only one']
        with self.assertRaisesRegex(ValueError, 'Party names'):
            check_vote_table(table)

    def test_single_election_xlsx_includes_party_names(self):
        import openpyxl

        table = load_votes('../data/iceland-2021.csv')
        system = self.make_system(table, 'max-const-seat-share')
        handler = ElectionHandler(table, [system], use_thresholds=True)
        with TemporaryDirectory() as directory:
            filename = Path(directory) / 'election.xlsx'
            handler.to_xlsx(filename)
            workbook = openpyxl.load_workbook(filename, read_only=True)
        worksheet = workbook['Party names']
        self.assertEqual(
            [worksheet['A1'].value, worksheet['B1'].value],
            ['Abbreviation', 'Name'],
        )
        self.assertEqual(
            [worksheet['A2'].value, worksheet['B2'].value],
            ['B', 'Framsóknarflokkur'],
        )

    def test_vote_table_xlsx_round_trip_preserves_party_names(self):
        table = load_votes('../data/iceland-2021.csv')
        with TemporaryDirectory() as directory:
            filename = Path(directory) / 'votes.xlsx'
            votes_to_excel(table, filename)
            loaded = load_votes(filename)
        self.assertEqual(loaded['party_names'], table['party_names'])

    def test_vote_table_xlsx_round_trip_preserves_adjustment_seat_maxima(self):
        import openpyxl

        table = load_votes('../data/2-by-2-example.csv')
        table['max_total_adj_seats'] = 6
        table['constituencies'][0]['max_adj_seats'] = 2
        table['constituencies'][1]['max_adj_seats'] = None
        with TemporaryDirectory() as directory:
            filename = Path(directory) / 'votes.xlsx'
            votes_to_excel(table, filename)
            workbook = openpyxl.load_workbook(filename, read_only=True)
            self.assertEqual(workbook.active['D4'].value, '-')
            workbook.close()
            loaded = load_votes(filename)
        self.assertEqual(loaded['max_total_adj_seats'], 6)
        self.assertEqual(
            [constituency['max_adj_seats']
             for constituency in loaded['constituencies']],
            [2, None],
        )

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

    def test_quota_includes_pruned_but_not_threshold_excluded_votes(self):
        cases = [
            ('hare', 36),
            ('droop', 70 - 170 / 6),
        ]
        for rule_name, second_value in cases:
            with self.subTest(rule=rule_name):
                _, seat_factory, _ = apportion1d_general(
                    v_votes=[70, 30],
                    num_total_seats=5,
                    prior_allocations=[],
                    rule=QUOTA_RULES[rule_name],
                    type_of_rule='Quota',
                    threshold_percent=30,
                    threshold_total=200,
                )
                seats = seat_factory()
                self.assertEqual(next(seats)['active_votes'], 70)
                self.assertAlmostEqual(next(seats)['active_votes'], second_value)

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

    def test_zero_list_votes_are_preserved_in_election_calculations(self):
        table = {
            'name': 'Zero-list example',
            'parties': ['A', 'B'],
            'votes': [[0, 100], [100, 0]],
            'constituencies': [
                {'name': 'I', 'num_fixed_seats': 1, 'num_adj_seats': 0},
                {'name': 'II', 'num_fixed_seats': 1, 'num_adj_seats': 0},
            ],
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
        system = self.make_system(table, 'max-const-seat-share')
        election = ElectionHandler(
            table, [system], use_thresholds=True).elections[0]

        np.testing.assert_array_equal(
            election.votes, [[0, 100], [100, 0]])
        np.testing.assert_array_equal(election.votesums, [100, 100])
        np.testing.assert_array_equal(
            election.const_threshold_totals, [100, 100])

    def test_common_allocation_does_not_add_forced_steps(self):
        table = {
            'name': 'Adjustment example',
            'parties': ['A', 'B'],
            'votes': [[100, 0], [0, 100]],
            'constituencies': [
                {'name': 'I', 'num_fixed_seats': 0, 'num_adj_seats': 1},
                {'name': 'II', 'num_fixed_seats': 0, 'num_adj_seats': 1},
            ],
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
        system = self.make_system(table, 'max-const-seat-share')
        election = ElectionHandler(
            table, [system], use_thresholds=True).elections[0]

        criteria_column = election.demo_tables[0]['headers'].index('Criteria')
        self.assertEqual(
            [row[criteria_column] for row in election.demo_tables[0]['steps']],
            ['Max over all lists', 'Max over all lists'],
        )

    def test_common_allocation_uses_logical_votes_without_changing_totals(self):
        table = {
            'name': 'Logical-vote example',
            'parties': ['A', 'B'],
            'votes': [[100, 0], [100, 0]],
            'constituencies': [
                {'name': 'I', 'num_fixed_seats': 0, 'num_adj_seats': 1},
                {'name': 'II', 'num_fixed_seats': 0, 'num_adj_seats': 1},
            ],
            'party_vote_basis': 'party_vote_info',
            'party_vote_info': {
                'name': 'National',
                'num_fixed_seats': 0,
                'num_adj_seats': 0,
                'votes': [100, 100],
                'specified': True,
                'total': 200,
                'pruned': 0,
            },
        }
        system = self.make_system(table, 'max-const-seat-share')
        election = ElectionHandler(
            table, [system], use_thresholds=True).elections[0]

        np.testing.assert_array_equal(election.votes, table['votes'])
        np.testing.assert_array_equal(election.votesums, [200, 0])
        np.testing.assert_array_equal(
            election.results['all_const_seats'], [[1, 0], [0, 1]])

    def test_norwegian_parties_must_have_votes_in_every_constituency(self):
        table = {
            'name': 'Norwegian standing example',
            'parties': ['A', 'B'],
            'votes': [[60, 100], [60, 0]],
            'constituencies': [
                {'name': 'I', 'num_fixed_seats': 1, 'num_adj_seats': 1},
                {'name': 'II', 'num_fixed_seats': 1, 'num_adj_seats': 1},
            ],
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
        system = self.make_system(table, 'norwegian-law', threshold=4)
        system['primary_divider'] = 'nordic-1.4'
        system['adj_determine_divider'] = 'nordic-1.4'
        system['adj_alloc_divider'] = 'sainte-lague'
        handler = ElectionHandler(table, [system], use_thresholds=True)
        election = handler.elections[0]

        np.testing.assert_array_equal(election.party_stands_everywhere, [True, False])
        np.testing.assert_array_equal(election.desired_col_sums, [3, 1])
        np.testing.assert_array_equal(election.results['all_const_total'], [3, 1])

        # Candidacy comes from the source table and does not change when a
        # simulated vote gives B positive votes in the second constituency.
        handler.run_elections(True, [[60, 100], [60, 50]])
        np.testing.assert_array_equal(election.desired_col_sums, [3, 1])

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
                table['party_vote_basis'] = basis
                system = self.make_system(table, 'max-const-seat-share')
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
        table['party_vote_basis'] = 'party_vote_info'
        system = self.make_system(table, 'max-const-seat-share', threshold=4)
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

    def test_run_elections_accepts_numpy_vote_matrix(self):
        table = load_votes('../data/2-by-2-example.csv')
        system = self.make_system(table, 'max-const-seat-share')
        handler = ElectionHandler(table, [system], use_thresholds=True)

        handler.run_elections(True, votes=np.asarray(table['votes']))

        self.assertEqual(
            sum(handler.elections[0].results['all_const_total']), 25)

    def test_old_vote_tables_default_to_no_pruned_votes(self):
        table = load_votes('../data/2-by-2-example.csv')
        table.pop('pruned')
        table['party_vote_info'].pop('pruned')
        checked = check_vote_table(table)
        self.assertEqual(checked['pruned'], [0, 0])
        self.assertEqual(checked['party_vote_info']['pruned'], 0)
        self.assertEqual(checked['party_vote_basis'], 'totals')

    def test_party_vote_basis_defaults_to_totals_without_party_votes(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['party_vote_basis'] = 'party_vote_info'
        checked = check_vote_table(table)
        self.assertEqual(checked['party_vote_basis'], 'totals')

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
        table['party_vote_basis'] = 'average'
        system = self.make_system(table, 'max-const-seat-share')
        handler = ElectionHandler(table, [system], use_thresholds=True)
        self.assertEqual(handler.elections[0].nat_votes.tolist(), [4000, 3850])

    def test_party_vote_basis_applies_to_all_systems(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['party_vote_info'] = {
            'name': 'National',
            'num_fixed_seats': 0,
            'num_adj_seats': 0,
            'votes': [4200, 3800],
            'specified': True,
            'total': 8000,
            'pruned': 0,
        }
        table['party_vote_basis'] = 'party_vote_info'
        first = self.make_system(table, 'max-const-seat-share')
        second = self.make_system(table, 'max-const-seat-share')
        second['seat_spec_options']['party'] = 'average'
        handler = ElectionHandler(table, [first, second], use_thresholds=True)
        for election in handler.elections:
            self.assertEqual(election.nat_votes.tolist(), [4200, 3800])
            self.assertEqual(
                election.system['seat_spec_options']['party'],
                'party_vote_info',
            )

    def test_old_json_uses_first_system_party_vote_basis(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['party_vote_info'] = {
            'name': 'National',
            'num_fixed_seats': 0,
            'num_adj_seats': 0,
            'votes': [4000, 4000],
            'specified': True,
            'total': 8000,
            'pruned': 0,
        }
        table.pop('party_vote_basis')
        system = self.make_system(table, 'max-const-seat-share')
        system['seat_spec_options']['party'] = 'average'
        contents = {
            'vote_table': table,
            'systems': [system],
            'sim_settings': SimulationSettings(),
        }
        with TemporaryDirectory() as directory:
            filename = Path(directory) / 'download-all.json'
            filename.write_text(json.dumps(contents), encoding='utf-8')
            loaded = load_json(filename)
        self.assertEqual(loaded['vote_table']['party_vote_basis'], 'average')

    def test_settings_download_preserves_adjustment_preparation(self):
        table = load_votes('../data/sweden_2018.csv')
        system = self.make_swedish_system(table)
        system['compare_with'] = False
        system['nat_seats'] = {
            'specified': False,
            'num_fixed_seats': 0,
            'num_adj_seats': 0,
        }
        app.config.update(TESTING=True)
        response = app.test_client().post('/api/settings/save/', json={
            'systems': [system],
            'sim_settings': SimulationSettings(),
        })
        saved = json.loads(response.data)
        saved_system = saved['e_settings'][0]
        self.assertEqual(
            saved_system['adjustment_preparation_method'], 'switching_se')
        self.assertEqual(
            saved_system['adjustment_preparation_rule'], 'nordic-1.2')
        self.assertEqual(
            saved_system['fixed_seat_eligibility'],
            'national-or-constituency')
        self.assertNotIn('additional_adjustment_method', saved_system)
        self.assertNotIn('additional_adjustment_allocation_rule', saved_system)

    def test_fractional_reference_ignores_thresholds_and_divider_rules(self):
        table = {
            'name': 'Fractional reference example',
            'parties': ['A', 'B'],
            'votes': [[60, 40], [60, 40]],
            'pruned': [0, 0],
            'constituencies': [
                {'name': 'I', 'num_fixed_seats': 0, 'num_adj_seats': 3},
                {'name': 'II', 'num_fixed_seats': 0, 'num_adj_seats': 4},
            ],
            'party_vote_info': {
                'name': '-',
                'num_fixed_seats': 0,
                'num_adj_seats': 0,
                'votes': [],
                'specified': False,
                'total': 0,
                'pruned': 0,
            },
            'party_vote_basis': 'totals',
        }
        system = self.make_system(table, 'max-const-seat-share', threshold=50)
        system['adj_determine_divider'] = 'dhondt'
        election = ElectionHandler(
            table, [system], use_thresholds=True).elections[0]
        election.calculate_ref_seat_shares('both')

        self.assertEqual(election.desired_col_sums.tolist(), [7, 0])
        np.testing.assert_allclose(election.fractional_party_seats, [4.2, 2.8])
        np.testing.assert_allclose(
            election.ref_seat_shares.sum(axis=0), [4.2, 2.8])
        np.testing.assert_allclose(election.ref_seat_shares.sum(axis=1), [3, 4])

    def test_fractional_reference_accounts_for_national_seats(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['party_vote_info'] = {
            'name': 'National',
            'num_fixed_seats': 0,
            'num_adj_seats': 2,
            'votes': [4500, 3500],
            'specified': True,
            'total': 8000,
            'pruned': 0,
        }
        table['party_vote_basis'] = 'party_vote_info'
        system = self.make_system(table, 'max-const-seat-share')
        election = ElectionHandler(
            table, [system], use_thresholds=True).elections[0]
        election.calculate_ref_seat_shares('both')

        np.testing.assert_allclose(
            election.total_ref_seat_shares, [15.1875, 11.8125])
        np.testing.assert_allclose(
            election.ref_seat_shares.sum(axis=1), [12, 13])
        self.assertAlmostEqual(election.total_ref_nat.sum(), 2)
        self.assertTrue((election.total_ref_nat >= 0).all())

    def test_simulation_reference_is_independent_of_system_order(self):
        table = load_votes('../data/2-by-2-example.csv')

        def systems():
            first = self.make_system(
                table, 'max-const-seat-share', threshold=50)
            first['name'] = 'Threshold system'
            first['adj_determine_divider'] = 'dhondt'
            second = self.make_system(
                table, 'max-const-seat-share', threshold=0)
            second['name'] = 'No-threshold system'
            second['adj_determine_divider'] = 'sainte-lague'
            return first, second

        settings = SimulationSettings()
        settings['simulation_count'] = 1
        settings['cpu_count'] = 1
        first, second = systems()
        simulations = [
            Simulation(settings, [first, second], table),
            Simulation(settings, list(reversed(systems())), table),
        ]

        references = []
        measures = []
        for simulation in simulations:
            references.append({
                election.system['name']: election.ref_seat_shares.copy()
                for election in simulation.reference_handler.elections
            })
            simulation.run_and_collect_measures(table['votes'], None)
            values = simulation.stat['sum_abs'].mean()
            measures.append(dict(zip(
                [system['name'] for system in simulation.systems], values)))

        for name in references[0]:
            np.testing.assert_allclose(references[0][name], references[1][name])
        np.testing.assert_allclose(
            references[0]['Threshold system'],
            references[0]['No-threshold system'],
        )
        self.assertEqual(measures[0], measures[1])

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
