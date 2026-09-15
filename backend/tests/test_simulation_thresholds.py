from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from dictionaries import ELECTION_LAW_PRESETS
from electionSystem import ElectionSystem
from noweb import load_votes
from simulate import Simulation, SimulationSettings, Sim_result


DATA = Path(__file__).resolve().parents[2] / 'data'
THRESHOLDS = ('constituency_threshold', 'adjustment_threshold',
              'adjustment_threshold_seats')


class SimulationThresholdTest(unittest.TestCase):
    def assert_threshold_modes_equal(self, table, systems, settings,
                                     check_statistics=True):
        allocations = []
        statistics = []
        for use_thresholds in (False, True):
            run_systems = deepcopy(systems)
            if use_thresholds:
                for system in run_systems:
                    system.update(dict.fromkeys(THRESHOLDS, 0))
            run_settings = deepcopy(settings)
            run_settings['use_thresholds'] = use_thresholds
            simulation = Simulation(run_settings, run_systems, deepcopy(table))
            observed = []
            run_and_collect = simulation.run_and_collect_measures

            def record(votes, party_votes, iteration):
                run_and_collect(votes, party_votes, iteration)
                observed.append(deepcopy({
                    'votes': votes, 'party_votes': party_votes,
                    'allocations': [e.results for e in simulation.election_handler.elections],
                }))

            with patch.object(simulation, 'run_and_collect_measures', side_effect=record):
                simulation.simulate(tasknr=1)
            self.assertEqual(len(observed), settings['simulation_count'])
            allocations.append(observed)
            if check_statistics:
                result = Sim_result(simulation.attributes())
                result.analysis()
                statistics.append({key: getattr(result, key) for key in (
                    'base_allocations', 'data', 'seat_data', 'vote_data',
                    'party_data', 'histogram_data',
                )})

        np.testing.assert_equal(allocations[0], allocations[1])
        if check_statistics:
            np.testing.assert_equal(statistics[0], statistics[1])

    def test_seeded_distributions_and_threshold_choices(self):
        for national_votes in (False, True):
            table = load_votes(DATA / '2-by-2-example.csv')
            table['pruned'] = [500, 300]
            if national_votes:
                table['party_vote_basis'] = 'average'
                table['party_vote_info'] = {
                    'name': 'National votes', 'votes': [4200, 3800],
                    'num_fixed_seats': 1, 'num_adj_seats': 1,
                    'specified': True, 'pruned': 800,
                }
            for choice in (0, 1):
                systems = []
                for index, rule in enumerate(('dhondt', 'sainte-lague')):
                    system = ElectionSystem()
                    system.copy_info_from_votes(table)
                    system.update(
                        name=f'System {index}', compare_with=index == 0,
                        primary_divider=rule, adj_determine_divider=rule,
                        constituency_threshold=45, adjustment_threshold=55,
                        adjustment_threshold_seats=8, adj_threshold_choice=choice)
                    systems.append(system)
                for distribution in ('log-normal', 'uniform', 'gamma', 'beta'):
                    with self.subTest(national_votes=national_votes, choice=choice,
                                      distribution=distribution):
                        settings = SimulationSettings()
                        settings.update(random_seed=24680, simulation_count=1,
                                        cpu_count=1, gen_method=distribution)
                        self.assert_threshold_modes_equal(table, systems, settings)

    def test_seeded_nordic_law_presets(self):
        cases = (
            ('iceland', 'icel-2024-mbl.csv'),
            ('norway', 'norway_2025.csv'),
            ('finland', 'finland_2023.csv'),
            ('sweden-2014', 'sweden_2014.csv'),
            ('sweden-2018', 'sweden_2022.csv'),
            ('denmark', 'denmark_2026.csv'),
        )
        for law, filename in cases:
            with self.subTest(law=law):
                table = load_votes(DATA / filename)
                system = ElectionSystem()
                system.copy_info_from_votes(table)
                preset = next(p['settings'] for p in ELECTION_LAW_PRESETS if p['value'] == law)
                system.update(deepcopy(preset))
                system['seat_spec_options']['const'] = system.pop('constituency_seat_specification')
                settings = SimulationSettings()
                settings.update(random_seed=24680, simulation_count=1, cpu_count=1)
                if law == 'finland':
                    settings['scaling'] = 'const'
                self.assert_threshold_modes_equal(
                    table, [system], settings, check_statistics=False)
