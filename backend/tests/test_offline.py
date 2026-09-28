import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from electionSystem import ElectionSystem
from input_files import load_votes
from offline import load_all_inputs, load_inputs, main
from simulate import SimulationSettings
from simulation_chunks import split_replicates


VOTES = Path(__file__).resolve().parents[2] / 'data' / '2-by-2-example.csv'


class OfflineSimulationTest(unittest.TestCase):
    def files(self, directory):
        system = ElectionSystem()
        system['name'] = 'Test system'
        systems = Path(directory) / 'systems.json'
        systems.write_text(json.dumps({'systems': [system]}), encoding='utf-8')
        settings = Path(directory) / 'settings.json'
        settings.write_text(json.dumps({'sim_settings': SimulationSettings()}),
                            encoding='utf-8')
        return systems, settings

    def test_input_overrides_and_sensitivity_defaults(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            _, _, parsed = load_inputs(VOTES, systems, settings, {
                'simulation_count': 5, 'cpu_count': 2, 'random_seed': 17,
            })
            self.assertEqual(parsed['simulation_count'], 5)
            self.assertEqual(parsed['cpu_count'], 2)
            self.assertEqual(parsed['random_seed'], 17)
            self.assertTrue(parsed['sensitivity'])
            self.assertEqual(parsed['sensitivity_covs'], [0.3, 1, 3])

    def test_spreadsheet_vote_input_is_rejected(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            spreadsheet = Path(directory) / 'votes.xlsx'
            with self.assertRaisesRegex(ValueError, 'Vote input must be a CSV file'):
                load_inputs(spreadsheet, systems, settings, {})

    def test_download_all_produces_same_csv_with_sensitivity(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            all_file = Path(directory) / 'download-all.json'
            all_file.write_text(json.dumps({
                'vote_table': load_votes(VOTES),
                'systems': json.loads(systems.read_text())['systems'],
                'sim_settings': json.loads(settings.read_text())['sim_settings'],
            }), encoding='utf-8')
            output = Path(directory) / 'results.csv'
            options = ['-o', str(output), '-r', '2', '-C', '1', '-S', '123']
            self.assertEqual(main(['-v', str(VOTES), '-e', str(systems),
                                   '-s', str(settings), *options]), 0)
            separate = output.read_bytes()
            self.assertEqual(main(['-a', str(all_file), *options]), 0)
            self.assertEqual(output.read_bytes(), separate)
            with output.open(newline='', encoding='utf-8') as file:
                rows = list(csv.reader(file))
            self.assertEqual(len([row for row in rows
                                  if row[0].startswith('Sensitivity:')]), 24)

    def test_chunk_ranges_cover_replicates_once(self):
        self.assertEqual(split_replicates(7, 3), [(3, 0), (2, 3), (2, 5)])

    def test_download_all_requires_votes(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            all_file = Path(directory) / 'settings-only.json'
            all_file.write_text(json.dumps({
                'systems': json.loads(systems.read_text())['systems'],
                'sim_settings': json.loads(settings.read_text())['sim_settings'],
            }), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Download all file'):
                load_all_inputs(all_file, {})

    def test_csv_has_means_standard_deviations_and_confidence_limits(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            output = Path(directory) / 'results.csv'
            arguments = [
                '-v', str(VOTES), '-e', str(systems),
                '-s', str(settings), '-o', str(output),
                '-r', '2', '-C', '1', '-S', '123',
            ]
            self.assertEqual(main(arguments), 0)
            with output.open(newline='', encoding='utf-8') as file:
                rows = list(csv.reader(file))
            self.assertEqual(rows[0], ['Measure', 'Statistic', 'Test system'])
            self.assertIn(['Party-total absolute deviation', 'Mean', rows[1][2]], rows)
            self.assertEqual(
                {row[1] for row in rows
                 if row[0] == "Greatest relative over-representation (D'Hondt)"},
                {'Mean', 'Standard deviation', '95% CI lower', '95% CI upper'},
            )
            self.assertEqual({row[1] for row in rows[1:]},
                             {'Mean', 'Standard deviation', '95% CI lower',
                              '95% CI upper'})
            sensitivity = [row for row in rows if row[0].startswith('Sensitivity:')]
            self.assertEqual(len(sensitivity), 2 * 3 * 4)
            self.assertTrue(all(row[2] != '' for row in sensitivity))
            first = output.read_bytes()
            self.assertEqual(main(arguments), 0)
            self.assertEqual(output.read_bytes(), first)

    def test_two_cpu_output_has_same_seeded_means(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            output = Path(directory) / 'results.csv'
            arguments = [
                '--votes', str(VOTES), '--systems', str(systems),
                '--settings', str(settings), '--output', str(output),
                '--replicates', '2', '--seed', '123',
            ]
            self.assertEqual(main(arguments + ['--cpus', '1']), 0)
            with output.open(newline='', encoding='utf-8') as file:
                single = list(csv.reader(file))
            self.assertEqual(main(arguments + ['--cpus', '2']), 0)
            with output.open(newline='', encoding='utf-8') as file:
                parallel = list(csv.reader(file))
            self.assertEqual([row[0:2] for row in parallel],
                             [row[0:2] for row in single])
            for left, right in zip(single[1:], parallel[1:]):
                if left[2] and right[2]:
                    self.assertAlmostEqual(float(left[2]), float(right[2]), places=8)
