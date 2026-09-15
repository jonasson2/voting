import csv
import unittest

import numpy as np

from apportion import apportion1d_general
from division_rules import dhondt_gen, hare, sainte_lague_gen
from dictionaries import ELECTION_LAW_PRESETS
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from methods import danish
from methods.icelandic_law import icelandic_apportionment
from methods.norwegian_law import norwegian_apportionment
from methods.switching_se import switching
from randomness import make_rng
from simulate import Simulation, SimulationSettings
from ties import TieReport
from vote_table import check_vote_table, process_vote_table
from web import app


class TieTest(unittest.TestCase):
    def table(self, rows):
        return check_vote_table(process_vote_table(list(csv.reader(rows)), 'test.csv'))

    def system(self, table):
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        return system

    def test_division_and_quota_choose_and_report_first_party(self):
        for rule, kind in [(dhondt_gen, 'Division'), (hare, 'Quota')]:
            report = TieReport()
            seats, _, _ = apportion1d_general(
                [100, 100], 1, [], rule, kind,
                on_tie=report.reporter('Fixed seats', ['A', 'B']))
            np.testing.assert_array_equal(seats, [1, 0])
            self.assertEqual(report.events[0]['candidates'], ['A', 'B'])
            self.assertEqual(report.events[0]['selected'], 'A')

    def test_no_report_for_unallocated_next_seat_or_near_tie(self):
        for votes, count in [([100, 50], 1), ([100, 100.0000001], 1)]:
            report = TieReport()
            apportion1d_general(votes, count, [], dhondt_gen,
                                on_tie=report.reporter('Fixed seats', ['A', 'B']))
            self.assertEqual(report.events, [])

    def test_repeated_ties_are_summarized_once(self):
        report = TieReport()
        apportion1d_general([100, 100], 10, [], dhondt_gen,
                            on_tie=report.reporter('Fixed seats', ['A', 'B']))
        self.assertEqual(len(report.events), 1)

    def test_single_election_api_reports_and_resets_ties(self):
        table = self.table(['Example,fixed,adj,A,B', 'North,1,0,100,100'])
        system = self.system(table)
        with app.test_client() as client:
            payload = {'vote_table': table, 'systems': [system]}
            first = client.post('/api/election/', json=payload).get_json()
            again = client.post('/api/election/', json=payload).get_json()
        self.assertEqual(first, again)
        self.assertEqual(first['results'][0]['ties'][0]['selected'], 'A')
        election = ElectionHandler(table, [system], True).elections[0]
        election.set_votes([[101, 100]])
        election.assign_seats()
        self.assertEqual(election.get_result_web()['ties'], [])

    def test_party_total_tie_is_reported_separately(self):
        table = self.table(['Example,fixed,adj,A,B', 'North,0,1,100,100'])
        election = ElectionHandler(table, [self.system(table)], True).elections[0]
        self.assertEqual(election.get_result_web()['ties'][0]['stage'], 'Party totals')

    def preset_election(self, table, preset):
        system = self.system(table)
        settings = next(p['settings'] for p in ELECTION_LAW_PRESETS
                        if p['value'] == preset)
        system.update({key: value for key, value in settings.items()
                       if key != 'constituency_seat_specification'})
        return ElectionHandler(table, [system], True).elections[0]

    def test_finnish_adjustment_as_fixed_tie_reaches_single_election_results(self):
        table = self.table(['Example,fixed,adj,A,B',
                            'North,0,1,100,100', 'South,0,2,300,400'])
        election = self.preset_election(table, 'finland')
        self.assertEqual(election.results['all_const_seats'], [[1, 0], [1, 1]])
        self.assertEqual(election.get_result_web()['ties'], [{
            'stage': 'Adjustment seats',
            'candidates': ['North: A', 'North: B'], 'selected': 'North: A',
        }])
        election.rng = make_rng(42)
        election.assign_seats()
        self.assertEqual(election.tie_report.events, [])

    def test_icelandic_fallback_party_tie_beyond_original_entitlements(self):
        table = self.table(['Example,fixed,adj,A,B,C',
                            'North,0,1,1000,0,0', 'South,0,2,0,100,100'])
        election = self.preset_election(table, 'iceland')
        # The initial three national entitlements all go to A, but A can only
        # take one seat. B and C tie further down the quotient sequence.
        np.testing.assert_array_equal(election.desired_col_sums, [3, 0, 0])
        self.assertEqual(election.results['all_const_seats'], [[1, 0, 0], [0, 1, 1]])
        self.assertEqual(election.get_result_web()['ties'], [{
            'stage': 'Adjustment-seat party order',
            'candidates': ['B', 'C'], 'selected': 'B',
        }])
        election.rng = make_rng(42)
        election.assign_seats()
        self.assertEqual(election.tie_report.events, [])

    def test_icelandic_fallback_ignores_party_without_an_available_constituency(self):
        table = self.table(['Example,fixed,adj,A,B,C',
                            'North,0,1,1000,100,0', 'South,0,1,0,0,100'])
        election = self.preset_election(table, 'iceland')
        self.assertEqual(election.results['all_const_seats'], [[1, 0, 0], [0, 0, 1]])
        self.assertEqual(election.get_result_web()['ties'], [])

    def test_simulated_elections_do_not_collect_tie_reports(self):
        table = self.table(['Example,fixed,adj,A,B',
                            'North,1,0,100,100', 'South,1,0,200,100'])
        settings = SimulationSettings()
        settings.update(cpu_count=1, simulation_count=1, random_seed=42)
        sim = Simulation(settings, [self.system(table)], table)
        sim.run_and_collect_measures(table['votes'], None)
        for handler in (sim.reference_handler, sim.election_handler):
            self.assertEqual(handler.elections[0].tie_report.events, [])

    def test_icelandic_and_norwegian_constituency_ties(self):
        for method in (icelandic_apportionment, norwegian_apportionment):
            report = TieReport()
            _, generator, _ = apportion1d_general([200, 200], 2, [], dhondt_gen)
            allocated, _ = method(
                np.array([[100, 100], [100, 100]]), [1, 1], [1, 1],
                np.zeros((2, 2), int), dhondt_gen,
                adj_seat_gen=generator, v_fixed_seats=[0, 0],
                on_tie=report.reporter('Adjustment seats', ['North A', 'North B', 'South A', 'South B']))
            np.testing.assert_array_equal(allocated, [[1, 0], [0, 1]])
            self.assertEqual(report.events[0]['selected'], 'North A')

    def test_danish_remaps_eligible_parties_and_regional_constituencies(self):
        report = TieReport()
        totals = danish.party_totals(np.array([1, 100, 100]), np.zeros(3, int),
                                    np.array([False, True, True]), 1, hare, 'Quota', None,
                                    report.reporter('Party totals', ['A', 'B', 'C']))
        np.testing.assert_array_equal(totals, [0, 1, 0])
        self.assertEqual(report.events[0]['candidates'], ['B', 'C'])
        report = TieReport()
        allocated, demo = danish.allocate_regions(
            np.full((3, 2), 100), np.zeros((3, 2), int), np.array([[1, 1], [1, 0]]),
            [{'abbreviation': 'R1', 'num_adj_seats': 2}, {'abbreviation': 'R2', 'num_adj_seats': 1}],
            [np.array([0, 2]), np.array([1])], np.zeros(3, int), [None] * 3,
            sainte_lague_gen, None,
            report.reporter('Adjustment seats', ['North A', 'North B', 'Mid A', 'Mid B', 'South A', 'South B']))
        self.assertEqual(report.events[0]['candidates'], ['North A', 'North B', 'South A', 'South B'])
        self.assertEqual(report.events[0]['selected'], 'North A')
        self.assertFalse(demo['data'][0]['lot'])
        self.assertTrue(demo['data'][0]['tie'])

    def test_swedish_removal_tie(self):
        report = TieReport()
        allocation, _ = switching(
            [[100, 100], [100, 100]], [3, 3], [3, 3],
            np.array([[2, 1], [2, 1]]), sainte_lague_gen,
            on_tie=report.reporter('Preparation', ['North A', 'North B', 'South A', 'South B']))
        np.testing.assert_array_equal(allocation, [[1, 2], [2, 1]])
        self.assertEqual(report.events[0]['candidates'], ['North A', 'South A'])
        self.assertEqual(report.events[0]['selected'], 'North A')
