import csv
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
        settings.update(simulation_count=4, cpu_count=2, random_seed=123)
        votes, systems, settings = prepare_inputs(
            votes, [system, other_system], settings, {})
        settings.update(sensitivity_covs=[50], sensitivity_simulation_count=5)

        uninterrupted = combine_chunks([
            run_chunk(votes, systems, settings, 4, 0)])
        with TemporaryDirectory() as directory:
            paths = [Path(directory) / f'chunk-{i}.json' for i in range(2)]
            for path, start in zip(paths, (0, 2)):
                write_chunk_result(path, run_chunk(
                    votes, systems, settings, 2, start))
            loaded = [read_chunk_result(path) for path in paths]
            self.assertEqual([result['start_iteration'] for result in loaded],
                             [0, 2])
            self.assertEqual([result['random_seed'] for result in loaded],
                             [123, 123])
            merged = combine_chunks(loaded)
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
            self.assertEqual(len(actual), len(expected))
            self.assertEqual(actual[0], expected[0])
            for left, right in zip(expected[1:], actual[1:]):
                self.assertEqual(left[:2], right[:2])
                for expected_value, actual_value in zip(left[2:], right[2:]):
                    if expected_value and actual_value:
                        self.assertAlmostEqual(
                            float(expected_value), float(actual_value), places=9)
                    else:
                        self.assertEqual(expected_value, actual_value)

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
