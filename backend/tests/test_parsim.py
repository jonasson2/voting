import csv
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from electionSystem import ElectionSystem
from input_files import load_votes
from offline import main as sim_main, prepare_inputs
from parsim.elja import split_counts
from simulate import SimulationSettings


ROOT = Path(__file__).resolve().parents[2]
VOTES = ROOT / 'data' / '2-by-2-example.csv'


class ParallelSimulationScriptsTest(unittest.TestCase):
    def test_replicates_follow_core_count_and_per_core_speed(self):
        nodes = [{'cores': 48, 'speed_per_core': 1.0},
                 {'cores': 64, 'speed_per_core': 1.0}]
        self.assertEqual(split_counts(100, nodes), [43, 57])
        nodes[1]['speed_per_core'] = 0.75
        self.assertEqual(split_counts(100, nodes), [50, 50])

    def command(self, script, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / 'backend' / 'parsim' / script),
             *map(str, args)],
            capture_output=True, text=True, check=False)

    def test_dash_seed_clears_saved_seed_before_master_chooses_one(self):
        settings = SimulationSettings()
        settings['random_seed'] = 77
        _, _, prepared = prepare_inputs(
            load_votes(VOTES), [ElectionSystem()], settings,
            {'random_seed': None})
        self.assertIsNone(prepared['random_seed'])

    def test_partition_launchers_share_all_replicates(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            all_file = base / 'all.json'
            all_file.write_text(json.dumps({
                'vote_table': load_votes(VOTES),
                'systems': [ElectionSystem()],
                'sim_settings': SimulationSettings(),
            }), encoding='utf-8')
            partitions = base / 'partitions.txt'
            partitions.write_text(
                'Nodes\tCores\tMaxNode\tSpeed\tPart\n'
                '1\t2\t1\t1\tfirst\n'
                '2\t4\t2\t2\tsecond\n', encoding='utf-8')
            output = base / 'distributed.csv'
            statistics = base / 'distributed.json'
            job_dir = base / 'job'
            completed = self.command(
                'elja.py', '-a', all_file, '-r', 6, '-i', 10, '-S', 123,
                '-n', 2, '-o', output, '-O', statistics, '--job-dir', job_dir,
                '--partitions', partitions, '--mode', 'local',
                '--local-cores', 2)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads((job_dir / 'manifest.json').read_text())
            self.assertEqual([node['partition'] for node in manifest['nodes']],
                             ['first', 'second'])
            self.assertEqual([node['replicates'] for node in manifest['nodes']],
                             [2, 4])
            self.assertEqual([node['start'] for node in manifest['nodes']],
                             [10, 12])
            self.assertEqual([node['cores'] for node in manifest['nodes']],
                             [2, 2])
            self.assertEqual(len(list(job_dir.glob('node-*.json'))), 2)
            merged = json.loads(statistics.read_text())['result']
            self.assertEqual((merged['start_iteration'],
                              merged['next_global_iteration'],
                              merged['iteration']), (10, 16, 6))

            direct = base / 'direct.csv'
            self.assertEqual(sim_main([
                '-a', str(all_file), '-r', '6', '-i', '10', '-C', '1',
                '-S', '123', '-o', str(direct),
            ]), 0)
            with output.open(newline='', encoding='utf-8') as file:
                distributed_rows = list(csv.reader(file))
            with direct.open(newline='', encoding='utf-8') as file:
                direct_rows = list(csv.reader(file))
            self.assertEqual(len(distributed_rows), len(direct_rows))
            self.assertEqual(distributed_rows[0], direct_rows[0])
            for distributed, single in zip(distributed_rows[1:], direct_rows[1:]):
                self.assertEqual(distributed[:2], single[:2])
                for left, right in zip(distributed[2:], single[2:]):
                    if left and right:
                        self.assertAlmostEqual(float(left), float(right), places=8)
                    else:
                        self.assertEqual(left, right)

    def test_slurm_launch_protocol_with_stub_commands(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            all_file = base / 'all.json'
            all_file.write_text(json.dumps({
                'vote_table': load_votes(VOTES),
                'systems': [ElectionSystem()],
                'sim_settings': SimulationSettings(),
            }), encoding='utf-8')
            partitions = base / 'partitions.txt'
            partitions.write_text(
                'Nodes\tCores\tMaxNode\tSpeed\tPart\n'
                '1\t2\t1\t1\tbusy\n'
                '2\t2\t2\t1\ttest\n', encoding='utf-8')
            fake_bin = base / 'bin'
            fake_bin.mkdir()
            salloc = fake_bin / 'salloc'
            salloc.write_text(
                '#!/usr/bin/env python3\n'
                'import os, subprocess, sys\n'
                'args = sys.argv[1:]\n'
                'if "--partition=busy" in args: sys.exit(1)\n'
                'if "--cpus-per-task=4" not in args: sys.exit(2)\n'
                'command = next(i for i, arg in enumerate(args) '
                'if not arg.startswith("--"))\n'
                'env = dict(os.environ, SLURM_JOB_NUM_NODES="1", '
                'SLURM_JOB_ID="12345")\n'
                'sys.exit(subprocess.run(args[command:], env=env).returncode)\n',
                encoding='utf-8')
            srun = fake_bin / 'srun'
            srun.write_text(
                '#!/usr/bin/env python3\n'
                'import os, subprocess, sys\n'
                'args = sys.argv[1:]\n'
                'if "--cpus-per-task=4" not in args: sys.exit(2)\n'
                'command = args.index("--exact") + 1\n'
                'if args[command:][args[command:].index("-C") + 1] != "2": '
                'sys.exit(3)\n'
                'sys.exit(subprocess.run(args[command:]).returncode)\n',
                encoding='utf-8')
            salloc.chmod(0o755)
            srun.chmod(0o755)
            output = base / 'report.csv'
            job_dir = base / 'job'
            completed = subprocess.run(
                [sys.executable, str(ROOT / 'backend' / 'parsim' / 'elja.py'),
                 '-a', str(all_file), '-r', '4', '-S', '123', '-n', '2',
                 '-o', str(output), '--job-dir', str(job_dir),
                 '--partitions', str(partitions), '--mode', 'slurm'],
                env={**os.environ, 'PATH': f'{fake_bin}:{os.environ["PATH"]}'},
                capture_output=True, text=True, check=False, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(output.exists())
            ready = json.loads((job_dir / 'allocation-000.json').read_text())
            self.assertEqual(ready['slurm_job_id'], '12345')
            manifest = json.loads((job_dir / 'manifest.json').read_text())
            self.assertEqual([node['partition'] for node in manifest['nodes']],
                             ['test', 'test'])
            self.assertEqual([node['cores'] for node in manifest['nodes']],
                             [2, 2])
            self.assertEqual([node['slurm_cpus'] for node in manifest['nodes']],
                             [4, 4])


if __name__ == '__main__':
    unittest.main()
