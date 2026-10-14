import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from electionSystem import ElectionSystem
from input_files import load_votes
from sim import prepare_inputs, write_csv
from simulate import SimulationSettings
from simulation_chunks import (
    combine_chunks, read_chunk_result, run_chunk, write_chunk_result,
)


class SimulationChunkDiskTest(unittest.TestCase):
    def test_saved_chunks_merge_like_uninterrupted_run(self):
        votes = load_votes(
            Path(__file__).resolve().parents[2] / 'data' / '2-by-2-example.csv')
        system = ElectionSystem()
        system['name'] = 'Test system'
        other_system = ElectionSystem()
        other_system['name'] = 'Second system'
        other_system['adj_alloc_divider'] = 'sainte-lague'
        settings = SimulationSettings()
        settings.update(simulation_count=5, cpu_count=2, random_seed=123,
                        sensitivity=True)
        votes, systems, settings = prepare_inputs(
            votes, [system, other_system], settings, {})
        settings.update(sensitivity_covs=[50], sensitivity_simulation_count=5)

        uninterrupted = combine_chunks([
            run_chunk(votes, systems, settings, 5, 37)])
        with TemporaryDirectory() as directory:
            paths = [Path(directory) / f'chunk-{i}.json' for i in range(2)]
            for path, (count, start) in zip(paths, ((2, 37), (3, 39))):
                write_chunk_result(path, run_chunk(
                    votes, systems, settings, count, start))
                payload = json.loads(path.read_text())
                self.assertEqual(payload['format_version'], 2)
                def assert_no_extrema(value):
                    if isinstance(value, dict):
                        self.assertFalse({'min', 'max', 'big', 'small'} & value.keys())
                        for child in value.values():
                            assert_no_extrema(child)
                    elif isinstance(value, list):
                        for child in value:
                            assert_no_extrema(child)
                assert_no_extrema(payload)
            loaded = [read_chunk_result(path) for path in paths]
            self.assertEqual([result['start_iteration'] for result in loaded],
                             [37, 39])
            self.assertEqual([result['iteration'] for result in loaded], [2, 3])
            self.assertEqual([result['random_seed'] for result in loaded],
                             [123, 123])
            merged = combine_chunks(loaded)
            self.assertEqual(merged.iteration, 5)
            for measure in ('sensitivity_between_parties',
                            'sensitivity_within_parties'):
                for statistic in ('avg', 'std', 'se', 'lo95', 'hi95'):
                    for expected, actual in zip(
                            uninterrupted.sensitivity_data[measure][statistic][0],
                            merged.sensitivity_data[measure][statistic][0]):
                        self.assertAlmostEqual(expected, actual, places=12)
            self.assertTrue(any(
                value > 0 for value in
                merged.sensitivity_data['sensitivity_between_parties']['std'][0]))

            expected_path = Path(directory) / 'expected.csv'
            actual_path = Path(directory) / 'actual.csv'
            write_csv(expected_path, uninterrupted)
            write_csv(actual_path, merged)
            with expected_path.open(newline='', encoding='utf-8') as file:
                expected = list(csv.reader(file))
            with actual_path.open(newline='', encoding='utf-8') as file:
                actual = list(csv.reader(file))
            self.assertEqual(actual, expected)

            from excel_util import simulation_to_xlsx
            from openpyxl import load_workbook
            excel_path = Path(directory) / 'result.xlsx'
            simulation_to_xlsx(merged.get_result_web(False), str(excel_path))
            workbook = load_workbook(excel_path, read_only=True)
            for sheet in workbook:
                values = {cell.value for row in sheet for cell in row
                          if isinstance(cell.value, str)}
                self.assertFalse({'MINIMUM', 'MAXIMUM', 'Minimum values',
                                  'Maximum values'} & values)
            workbook.close()

            _, combined_statistics = combine_chunks(
                [read_chunk_result(path) for path in paths], return_statistics=True)
            combined_path = Path(directory) / 'combined.json'
            write_chunk_result(combined_path, combined_statistics)
            assert_no_extrema(json.loads(combined_path.read_text()))
            restored = combine_chunks([read_chunk_result(combined_path)])
            self.assertEqual(restored.iteration, merged.iteration)
            self.assertEqual(restored.sensitivity_data, merged.sensitivity_data)

    def test_old_statistics_format_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            path.write_text(json.dumps({'format_version': 1, 'result': {'stat': {}}}))
            with self.assertRaisesRegex(ValueError, 'Unrecognized'):
                read_chunk_result(path)

    def test_failed_write_preserves_previous_result(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'chunk.json'
            path.write_text('previous result', encoding='utf-8')
            with self.assertRaisesRegex(TypeError, 'Cannot save object'):
                write_chunk_result(path, {'stat': object()})
            self.assertEqual(path.read_text(encoding='utf-8'),
                             'previous result')
            self.assertEqual(list(Path(directory).iterdir()), [path])


if __name__ == '__main__':
    unittest.main()
