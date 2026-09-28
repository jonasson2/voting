from io import BytesIO
import json
import unittest

from electionSystem import ElectionSystem
from input_files import prepare_simulation_inputs
from noweb import load_votes
from simulate import SimulationSettings
from web import app


class FileSectionsTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def upload(self, path, contents):
        data = BytesIO(json.dumps(contents).encode('utf-8'))
        return self.client.post(path, data={'file': (data, 'test.json')},
                                content_type='multipart/form-data').json

    def system(self):
        system = ElectionSystem()
        system['name'] = 'A test system'
        system['constituencies'] = []
        system['nat_seats'] = {'specified': False, 'num_fixed_seats': 0,
                               'num_adj_seats': 0}
        return system

    def test_system_download_and_upload_contain_only_systems(self):
        system = self.system()
        system['compare_with'] = False
        response = self.client.post('/api/systems/save/',
                                    json={'systems': [system],
                                          'sim_settings': SimulationSettings()})
        saved = json.loads(response.data)
        response.close()
        self.assertEqual(set(saved), {'systems'})
        self.assertNotIn('compare_with', saved['systems'][0])
        self.assertEqual(self.upload('/api/systems/upload/', saved), saved)
        self.assertIn('error', self.upload('/api/systems/upload/',
                                         {'systems': [system],
                                          'sim_settings': SimulationSettings()}))

    def test_settings_download_and_upload_contain_only_settings(self):
        settings = SimulationSettings()
        settings['const_rsd'] = 0.25
        settings['sensitivity'] = True
        response = self.client.post('/api/simulation-settings/save/',
                                    json={'sim_settings': settings,
                                          'systems': [self.system()]})
        saved = json.loads(response.data)
        response.close()
        self.assertEqual(set(saved), {'sim_settings'})
        self.assertEqual(saved['sim_settings']['const_rsd'], 0.25)
        self.assertEqual(self.upload('/api/simulation-settings/upload/', saved), saved)
        self.assertIn('error', self.upload('/api/simulation-settings/upload/',
                                         {'systems': [self.system()],
                                          'sim_settings': settings}))

    def test_section_uploads_reject_obsolete_fields(self):
        system = self.system()
        system['seat_spec_option'] = 'refer'
        result = self.upload('/api/systems/upload/', {'systems': [system]})
        self.assertIn('Obsolete electoral-system field', result['error'])
        settings = SimulationSettings()
        settings['const_cov'] = 0.2
        result = self.upload('/api/simulation-settings/upload/',
                             {'sim_settings': settings})
        self.assertIn('Obsolete simulation setting', result['error'])

    def test_all_file_round_trips_all_three_sections(self):
        contents = {
            'vote_table': load_votes('../data/2-by-2-example.csv'),
            'systems': [self.system()],
            'sim_settings': SimulationSettings(),
        }
        response = self.client.post('/api/saveall/', json=contents)
        saved = json.loads(response.data)
        response.close()
        self.assertEqual(set(saved), {'vote_table', 'systems', 'sim_settings'})
        uploaded = self.upload('/api/uploadall/', saved)
        self.assertEqual(set(uploaded), set(saved))
        self.assertEqual(uploaded['vote_table']['name'], saved['vote_table']['name'])
        self.assertEqual(uploaded['systems'][0]['name'], saved['systems'][0]['name'])
        self.assertEqual(uploaded['sim_settings']['simulation_count'],
                         saved['sim_settings']['simulation_count'])

    def test_simulation_preparation_fills_constituencies(self):
        votes = load_votes('../data/2-by-2-example.csv')
        system = ElectionSystem()
        self.assertNotIn('constituencies', system)
        _, systems, _ = prepare_simulation_inputs(
            votes, [system], SimulationSettings())
        self.assertEqual(systems[0]['constituencies'], votes['constituencies'])
