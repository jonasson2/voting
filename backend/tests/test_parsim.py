import csv
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from electionSystem import ElectionSystem
from input_files import load_votes
from offline import main as sim_main, prepare_inputs
from simulate import SimulationSettings


ROOT = Path(__file__).resolve().parents[2]
VOTES = ROOT / 'data' / '2-by-2-example.csv'


class ParallelSimulationScriptsTest(unittest.TestCase):
    def command(self, script, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / 'parsim' / script), *map(str, args)],
            capture_output=True, text=True, check=False)

    def test_dash_seed_clears_saved_seed_before_master_chooses_one(self):
        settings = SimulationSettings()
        settings['random_seed'] = 77
        _, _, prepared = prepare_inputs(
            load_votes(VOTES), [ElectionSystem()], settings,
            {'random_seed': None})
        self.assertIsNone(prepared['random_seed'])

    def test_master_worker_merge_and_retry(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            first = ElectionSystem()
            first['name'] = 'First'
            second = ElectionSystem()
            second['name'] = 'Second'
            second['adj_alloc_divider'] = 'sainte-lague'
            systems = base / 'systems.json'
            systems.write_text(json.dumps({'systems': [first, second]}),
                               encoding='utf-8')
            settings = base / 'settings.json'
            settings.write_text(json.dumps({
                'sim_settings': SimulationSettings()}), encoding='utf-8')
            all_file = base / 'all.json'
            all_file.write_text(json.dumps({
                'vote_table': load_votes(VOTES),
                'systems': [first, second],
                'sim_settings': SimulationSettings(),
            }), encoding='utf-8')
            job_dir = base / 'job'
            output = base / 'parallel.csv'
            arguments = [
                '-a', all_file,
                '-o', output, '-r', 4, '-C', 2, '-S', 123,
                '--chunk-size', 2, '--job-dir', job_dir,
            ]
            completed = self.command('run.py', *arguments)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads((job_dir / 'manifest.json').read_text())
            self.assertEqual(manifest['seed'], 123)
            self.assertEqual([(item['start'], item['count'])
                              for item in manifest['chunks']], [(0, 2), (2, 2)])

            expected = base / 'single.csv'
            self.assertEqual(sim_main([
                '-v', str(VOTES), '-e', str(systems), '-s', str(settings),
                '-o', str(expected), '-r', '4', '-C', '1', '-S', '123',
            ]), 0)
            with expected.open(newline='', encoding='utf-8') as file:
                single_rows = list(csv.reader(file))
            with output.open(newline='', encoding='utf-8') as file:
                parallel_rows = list(csv.reader(file))
            self.assertEqual(single_rows[0], parallel_rows[0])
            for single, parallel in zip(single_rows[1:], parallel_rows[1:]):
                self.assertEqual(single[:2], parallel[:2])
                for left, right in zip(single[2:], parallel[2:]):
                    if left and right:
                        self.assertAlmostEqual(float(left), float(right), places=8)
                    else:
                        self.assertEqual(left, right)

            chunk = job_dir / 'chunk-000001.json'
            chunk.unlink()
            missing = self.command('merge.py', job_dir, '-o', base / 'retry.csv')
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn('missing', missing.stderr)
            self.assertEqual(self.command('worker.py', job_dir, 1).returncode, 0)

            record = json.loads(chunk.read_text(encoding='utf-8'))
            record['metadata']['job_sha256'] = 'wrong'
            chunk.write_text(json.dumps(record), encoding='utf-8')
            mismatched = self.command('merge.py', job_dir, '-o', base / 'retry.csv')
            self.assertNotEqual(mismatched.returncode, 0)
            self.assertIn('another job', mismatched.stderr)
            self.assertEqual(self.command('worker.py', job_dir, 1).returncode, 0)
            merged = self.command('merge.py', job_dir, '-o', base / 'retry.csv')
            self.assertEqual(merged.returncode, 0, merged.stderr)
            self.assertEqual((base / 'retry.csv').read_bytes(), output.read_bytes())


if __name__ == '__main__':
    unittest.main()
