import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from electionSystem import ElectionSystem
from input_files import load_votes
from sim import load_all_inputs, load_inputs, main, run_simulation, write_csv
from simulate import SimulationSettings
from simulation_chunks import combine_chunks, read_chunk_result, split_replicates


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
        self.assertEqual(split_replicates(7, 3, 10),
                         [(3, 10), (2, 13), (2, 15)])

    def test_first_replicate_is_independent_of_cpu_count(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            statfile = Path(directory) / 'statistics.json'
            parallel = Path(directory) / 'parallel.csv'
            single = Path(directory) / 'single.csv'
            arguments = [
                '-v', str(VOTES), '-e', str(systems), '-s', str(settings),
                '-r', '4', '-S', '123', '-i', '7',
            ]
            self.assertEqual(main([
                *arguments, '-C', '2', '-O', str(statfile),
                '-o', str(parallel),
            ]), 0)
            saved = read_chunk_result(statfile)
            self.assertEqual((saved['start_iteration'],
                              saved['next_global_iteration'], saved['iteration']),
                             (7, 11, 4))
            self.assertEqual(main([
                *arguments, '-C', '1', '-o', str(single),
            ]), 0)
            with parallel.open(newline='', encoding='utf-8') as file:
                parallel_rows = list(csv.reader(file))
            with single.open(newline='', encoding='utf-8') as file:
                single_rows = list(csv.reader(file))
            self.assertEqual(len(parallel_rows), len(single_rows))
            self.assertEqual(parallel_rows[0], single_rows[0])
            for left, right in zip(parallel_rows[1:], single_rows[1:]):
                self.assertEqual(left[:2], right[:2])
                for a, b in zip(left[2:], right[2:]):
                    if a and b:
                        self.assertAlmostEqual(float(a), float(b), places=9)
                    else:
                        self.assertEqual(a, b)

    def test_statistics_output_can_be_read_and_reported(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            statfile = Path(directory) / 'statistics.json'
            report = Path(directory) / 'from-statistics.csv'
            direct = Path(directory) / 'direct.csv'
            arguments = [
                '-v', str(VOTES), '-e', str(systems), '-s', str(settings),
                '-r', '4', '-C', '2', '-S', '123',
            ]
            self.assertEqual(main([*arguments, '-O', str(statfile)]), 0)
            saved = read_chunk_result(statfile)
            self.assertEqual(saved['iteration'], 4)
            self.assertEqual(saved['sim_count'], 4)
            self.assertEqual(saved['random_seed'], 123)
            self.assertEqual(saved['start_iteration'], 0)
            self.assertEqual(saved['next_global_iteration'], 4)
            write_csv(report, combine_chunks([saved]))
            self.assertEqual(main([*arguments, '-o', str(direct)]), 0)
            self.assertEqual(report.read_bytes(), direct.read_bytes())
            self.assertEqual(main([
                *arguments, '-o', str(report), '-O', str(statfile),
            ]), 0)
            self.assertEqual(report.read_bytes(), direct.read_bytes())

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
            for label in (
                    'Party-total absolute deviation',
                    'Constituency-list absolute deviation',
                    'Geographical seat displacement',
                    'Constituency disparity',
                    "Maximum relative over-representation (D'Hondt)",
                    'Maximum seat-share surplus',
                    'Maximum seat-share shortfall'):
                measure_rows = [row for row in rows if row[0] == label]
                self.assertEqual(len(measure_rows), 4)
                self.assertTrue(all(row[2] != '' for row in measure_rows))
            relative = [row for row in rows
                        if row[0] == 'Entropy relative to system 1']
            self.assertEqual(len(relative), 4)
            self.assertTrue(all(row[2] == '' for row in relative))
            self.assertIn(['Party-total absolute deviation', 'Mean', rows[1][2]], rows)
            self.assertEqual(
                {row[1] for row in rows
                 if row[0] == "Maximum relative over-representation (D'Hondt)"},
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

    def test_relative_entropy_is_a_ratio_and_survives_statistics_reload(self):
        with TemporaryDirectory() as directory:
            systems_path, settings_path = self.files(directory)
            systems = json.loads(systems_path.read_text())['systems']
            systems.append(dict(systems[0], name='Compatible system'))
            systems.append(dict(systems[0], name='Different divisor',
                                adj_alloc_divider='sainte-lague'))
            systems_path.write_text(json.dumps({'systems': systems}),
                                    encoding='utf-8')
            votes, systems, settings = load_inputs(
                VOTES, systems_path, settings_path,
                {'simulation_count': 4, 'cpu_count': 1, 'random_seed': 123})
            result = run_simulation(votes, systems, settings)
            output = Path(directory) / 'results.csv'
            statfile = Path(directory) / 'statistics.json'
            self.assertEqual(main([
                '-v', str(VOTES), '-e', str(systems_path),
                '-s', str(settings_path), '-r', '4', '-C', '1', '-S', '123',
                '-o', str(output), '-O', str(statfile),
            ]), 0)
            direct = output.read_bytes()
            with output.open(newline='', encoding='utf-8') as file:
                relative = [row for row in csv.reader(file)
                            if row[0] == 'Entropy relative to system 1']
            self.assertEqual(len(relative), 4)
            statistics = ('avg', 'std', 'lo95', 'hi95')
            for row, statistic in zip(relative, statistics):
                self.assertEqual(row[4], '')
                for index in range(2):
                    self.assertEqual(float(row[index + 2]),
                                     result.data[index]['entropy_relative'][statistic])
            self.assertEqual(relative[0][2:4], ['1.0', '1.0'])
            write_csv(output, combine_chunks([read_chunk_result(statfile)]))
            self.assertEqual(output.read_bytes(), direct)

    def test_two_cpu_output_has_same_seeded_means(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            output = Path(directory) / 'results.csv'
            arguments = [
                '--votes', str(VOTES), '--systems', str(systems),
                '--settings', str(settings), '--csv', str(output),
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
