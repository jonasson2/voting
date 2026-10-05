import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from electionSystem import ElectionSystem
from input_files import load_votes
from sim import format_csv_entry, load_all_inputs, load_inputs, main, run_simulation, write_csv
from simulate import SimulationSettings
from simulation_chunks import combine_chunks, read_chunk_result, split_replicates


VOTES = Path(__file__).resolve().parents[2] / 'data' / '2-by-2-example.csv'


class OfflineSimulationTest(unittest.TestCase):
    def test_csv_precision_applies_to_values_and_confidence_intervals(self):
        display = {'fractional_digits': 4, 'percentage_digits': 2}
        entry = {'value': 1.234567, 'ci': 0.012345}
        self.assertEqual(format_csv_entry(entry, display), '1.2346 ± 0.0123')
        self.assertEqual(format_csv_entry(dict(entry, percentage=True), display),
                         '123.46 ± 1.23')
        self.assertEqual(format_csv_entry(dict(entry, integer=True, ci=None), display), '1')
        self.assertEqual(format_csv_entry('–', display), '–')
        self.assertEqual(format_csv_entry(entry, {'fractional_digits': 0, 'percentage_digits': 0}),
                         '1 ± 0')

    def test_download_all_precision_reaches_csv_and_old_files_use_defaults(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            contents = {
                'vote_table': load_votes(VOTES),
                'systems': json.loads(systems.read_text())['systems'],
                'sim_settings': json.loads(settings.read_text())['sim_settings'],
            }
            all_file = Path(directory) / 'all.json'
            all_file.write_text(json.dumps(contents), encoding='utf-8')
            overrides = {'simulation_count': 2, 'cpu_count': 1, 'random_seed': 123}
            votes, systems, settings, display = load_all_inputs(all_file, overrides)
            self.assertEqual(display, {'fractional_digits': 3, 'percentage_digits': 1})
            result = run_simulation(votes, systems, settings)
            contents['display_settings'] = {'fractional_digits': 5, 'percentage_digits': 2,
                                            'decimal_separator': ',', 'thousands_separator': '.'}
            all_file.write_text(json.dumps(contents), encoding='utf-8')
            expected = Path(directory) / 'expected.csv'
            output = Path(directory) / 'output.csv'
            result.input_files = {'Download all file': str(all_file)}
            write_csv(expected, result, contents['display_settings'])
            self.assertEqual(main(['-a', str(all_file), '-r', '2', '-C', '1', '-S', '123',
                                   '-o', str(output)]), 0)
            self.assertEqual(output.read_bytes(), expected.read_bytes())

    def files(self, directory):
        system = ElectionSystem()
        system['name'] = 'Test system'
        systems = Path(directory) / 'systems.json'
        systems.write_text(json.dumps({'systems': [system]}), encoding='utf-8')
        settings = Path(directory) / 'settings.json'
        settings.write_text(json.dumps({'sim_settings': dict(SimulationSettings(), sensitivity=True,
                                                    sensitivity_covs=[0.3, 1, 3])}),
                            encoding='utf-8')
        return systems, settings

    def test_input_overrides_preserve_sensitivity_settings(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            _, _, parsed, display = load_inputs(VOTES, systems, settings, {
                'simulation_count': 5, 'cpu_count': 2, 'random_seed': 17,
            })
            self.assertEqual(parsed['simulation_count'], 5)
            self.assertEqual(parsed['cpu_count'], 2)
            self.assertEqual(parsed['random_seed'], 17)
            self.assertTrue(parsed['sensitivity'])
            self.assertEqual(parsed['sensitivity_covs'], [0.3, 1, 3])
            self.assertEqual(display, {'fractional_digits': 3, 'percentage_digits': 1})

    def test_disabled_sensitivity_is_preserved(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            contents = json.loads(settings.read_text())
            contents['sim_settings'].update(
                sensitivity=False, sensitivity_covs=[0.01, 0.1],
                sensitivity_gen_method='uniform')
            settings.write_text(json.dumps(contents), encoding='utf-8')
            _, _, parsed, _ = load_inputs(VOTES, systems, settings, {})
            self.assertFalse(parsed['sensitivity'])
            self.assertEqual(parsed['sensitivity_covs'], [0.01, 0.1])
            self.assertEqual(parsed['sensitivity_gen_method'], 'uniform')

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
            def measures(contents):
                return contents[contents.index(b'Sum over reference seat share differences'):]
            self.assertEqual(measures(output.read_bytes()), measures(separate))
            with output.open(newline='', encoding='utf-8') as file:
                rows = list(csv.reader(file))
            self.assertEqual(len([row for row in rows
                                  if row[0].endswith('% CoV')]), 6)

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
            self.assertEqual(parallel_rows, single_rows)
            summary = {row[0]: row[1:] for row in parallel_rows}
            self.assertEqual(summary['Votes file'], [str(VOTES)])
            self.assertEqual(summary['Electoral systems file'], [str(systems)])
            self.assertEqual(summary['Simulation settings file'], [str(settings)])
            self.assertEqual(summary['Number of replicates'], ['4'])
            self.assertEqual(summary['Random seed'], ['123'])
            self.assertEqual(summary['First replicate number (zero-based)'], ['7'])
            self.assertEqual(summary['Sensitivity measures calculated'], ['yes'])
            self.assertEqual(summary['Sensitivity CoVs (%)'], ['0.3, 1, 3'])
            self.assertIn('Generating method', summary)
            self.assertIn('Relative standard deviation for list votes', summary)
            self.assertIn('Thresholds used', summary)
            self.assertIn('Scaling of votes for fractional reference seat shares', summary)

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

    def test_progress_preserves_results_for_one_and_multiple_cpus(self):
        with TemporaryDirectory() as directory:
            systems, settings = self.files(directory)
            output = Path(directory) / 'results.csv'
            progress = Path(directory) / 'progress.json'
            arguments = ['-v', str(VOTES), '-e', str(systems), '-s', str(settings),
                         '-r', '4', '-S', '123', '-i', '7', '-o', str(output)]
            self.assertEqual(main([*arguments, '-C', '1']), 0)
            baseline = output.read_bytes()
            for cpus in ('1', '2'):
                with self.subTest(cpus=cpus):
                    self.assertEqual(main([*arguments, '-C', cpus,
                                           '--progress', str(progress)]), 0)
                    self.assertEqual(output.read_bytes(), baseline)
                    status = json.loads(progress.read_text())
                    self.assertEqual(status['completed'], 4)
                    self.assertEqual(status['assigned'], 4)
                    self.assertGreater(status['elapsed'], 0)
            with self.assertRaises(SystemExit):
                main([*arguments, '--progress', str(output)])

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

    def test_csv_matches_web_rows_and_headings(self):
        with TemporaryDirectory() as directory:
            systems_path, settings_path = self.files(directory)
            votes, systems, settings, _ = load_inputs(
                VOTES, systems_path, settings_path,
                {'simulation_count': 2, 'cpu_count': 1, 'random_seed': 123})
            result = run_simulation(votes, systems, settings)
            output = Path(directory) / 'results.csv'
            write_csv(output, result)
            with output.open(newline='', encoding='utf-8') as file:
                rows = list(csv.reader(file))
            start = next(index for index, row in enumerate(rows)
                         if row[0] == 'Sum over reference seat share differences')
            self.assertEqual(rows[start:start+2], [
                ['Sum over reference seat share differences', '', 'STD.DEV.'],
                ['', 'Test system', 'Test system'],
            ])
            table = result.get_result_web(parallel=False)['vuedata']
            for group in table['group_ids']:
                if not table['show'][group]:
                    continue
                if table['group_titles'][group]:
                    self.assertTrue(any(row[0] == table['group_titles'][group]
                                        for row in rows))
                for row in table[group]:
                    stats = table['group_stats'].get(group, table['stats'])
                    expected = [row['rowtitle']]
                    for stat in stats:
                        entry = row[stat][0]
                        scale = 100 if entry.get('percentage') else 1
                        digits = 1 if entry.get('percentage') else 0 if entry.get('integer') else 3
                        cell = f"{scale * entry['value']:.{digits}f}"
                        if entry['ci'] is not None:
                            cell += f" ± {scale * entry['ci']:.{digits}f}"
                        expected.append(cell)
                    self.assertIn(expected, rows)
            self.assertNotIn(['Quality measures'], rows)
            self.assertNotIn(['Average & 95% confidence interval'], rows)
            self.assertEqual(sum(row[0].endswith('% CoV') for row in rows), 6)
            self.assertFalse(any('all seats as fixed' in row[0] for row in rows))

    def test_relative_entropy_is_a_ratio_and_survives_statistics_reload(self):
        with TemporaryDirectory() as directory:
            systems_path, settings_path = self.files(directory)
            systems = json.loads(systems_path.read_text())['systems']
            systems.append(dict(systems[0], name='Compatible system'))
            systems.append(dict(systems[0], name='Different divisor',
                                adj_alloc_divider='sainte-lague'))
            systems_path.write_text(json.dumps({'systems': systems}),
                                    encoding='utf-8')
            votes, systems, settings, _ = load_inputs(
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
                rows = list(csv.reader(file))
                relative = [row for row in rows
                            if row[0] == 'Entropy relative to system 1']
            self.assertEqual(len(relative), 1)
            self.assertFalse(any("Difference" in row for row in rows))
            self.assertEqual(relative[0], [
                'Entropy relative to system 1',
                '1.000 ± 0.000', '1.000 ± 0.000', '–',
                '0.000', '0.000', '–',
            ])
            sensitivity = [row for row in rows if row[0].endswith('% CoV')]
            self.assertEqual(len(sensitivity), 6)
            self.assertTrue(all(len(row) == 4 for row in sensitivity))
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
            self.assertEqual(parallel, single)
