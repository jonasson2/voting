from contextlib import ExitStack, redirect_stderr, redirect_stdout
from copy import deepcopy
from io import StringIO
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from electionSystem import ElectionSystem
from input_files import load_votes
from sim import prepare_inputs
from parsim import elja, worker
from parsim.elja import build_assignments, split_counts
from simulate import SimulationSettings
from simulation_chunks import read_chunk_result


ROOT = Path(__file__).resolve().parents[2]
VOTES = ROOT / 'data' / '2-by-2-example.csv'


class ParallelSimulationScriptsTest(unittest.TestCase):
    def test_excel_option_allows_excel_only_and_preserves_precision(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / 'all.json'
            source.write_text(json.dumps({
                'vote_table': load_votes(VOTES),
                'systems': [ElectionSystem()],
                'sim_settings': SimulationSettings(),
                'display_settings': {'fractional_digits': 5, 'percentage_digits': 2},
            }))
            for option in ('-x', '--excel'):
                with self.subTest(option=option), patch.object(elja, 'run_distributed') as run:
                    self.assertEqual(elja.main([
                        '-n', '2', '-a', str(source), option, 'results.xlsx']), 0)
                    arguments = run.call_args.kwargs
                    self.assertEqual(arguments['excel_path'], 'results.xlsx')
                    self.assertIsNone(arguments['csv_path'])
                    self.assertIsNone(arguments['stat_path'])
                    self.assertEqual(arguments['display_settings'],
                                     {'fractional_digits': 5, 'percentage_digits': 2})

    def test_outputs_cannot_share_a_path(self):
        for first, second in (('-o', '-x'), ('-x', '-O'), ('-o', '-O')):
            errors = StringIO()
            with self.subTest(outputs=(first, second)), redirect_stderr(errors):
                with self.assertRaises(SystemExit) as raised:
                    elja.main(['-n', '2', '-a', 'unused.json',
                               first, 'results', second, './results'])
            self.assertEqual(raised.exception.code, 2)
            self.assertIn('files must have different paths', errors.getvalue())

    def test_more_than_thirty_nodes_exits_before_loading_inputs(self):
        errors = StringIO()
        with redirect_stderr(errors), patch.dict(sys.modules, {'sim': None}), \
                patch.object(elja, 'run_distributed') as run:
            with self.assertRaises(SystemExit) as raised:
                elja.main(['-n', '31', '-a', 'missing.json', '-o', 'out.csv'])
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(errors.getvalue(),
                         'elja: -n must be 30 or less (Slurm job limit)\n')
        run.assert_not_called()

    def test_replicates_follow_core_count_and_per_core_speed(self):
        nodes = [{'cores': 48, 'speed_per_core': 1.0},
                 {'cores': 64, 'speed_per_core': 1.0}]
        self.assertEqual(split_counts(100, nodes), [43, 57])
        nodes[1]['speed_per_core'] = 0.75
        self.assertEqual(split_counts(100, nodes), [50, 50])

    def test_weighted_counts_and_ranges_with_rounding(self):
        capacities = [64, 48, 32]
        template = [{'cores': 64, 'speed_per_core': 1},
                    {'cores': 48, 'speed_per_core': 1},
                    {'cores': 64, 'speed_per_core': 0.5}]
        for total in (3, 4, 17, 1440, 1441):
            with self.subTest(replicates=total):
                nodes = build_assignments(total, deepcopy(template), 37)
                counts = [node['replicates'] for node in nodes]
                self.assertEqual(sum(counts), total)
                end = 37
                for node, capacity in zip(nodes, capacities):
                    self.assertIsInstance(node['replicates'], int)
                    self.assertGreaterEqual(node['replicates'], 1)
                    self.assertEqual(node['start'], end)
                    end += node['replicates']
                    if total >= 1440:
                        self.assertLessEqual(
                            abs(node['replicates'] - total * capacity / 144), 1)
                self.assertEqual(end, 37 + total)

    def test_too_few_replicates_for_nodes(self):
        with self.assertRaisesRegex(ValueError, 'at least the number of nodes'):
            split_counts(1, [{'cores': 2, 'speed_per_core': 1}] * 2)

    def test_slurm_submission_command(self):
        log = StringIO()
        with patch.object(elja.subprocess, 'Popen') as launch:
            process = elja.launch_node(
                Path('/job'), 3, 'mimir', 128, 5, log)
        launch.assert_called_once_with([
            'salloc', '--immediate=5', '--exclusive', '--mem=0',
            '--partition=mimir', '--nodes=1', '--ntasks=1',
            '--cpus-per-task=128', '--job-name=parsim-003',
            sys.executable, str(elja.HERE / 'worker.py'),
            '--job-dir', '/job', '--node-id', '3',
        ], stdin=subprocess.DEVNULL, stdout=log, stderr=log,
            start_new_session=True)
        self.assertIs(process, launch.return_value)

    def test_elja_environment_is_used_for_workers(self):
        with TemporaryDirectory() as directory:
            here = Path(directory) / 'backend' / 'parsim'
            python = Path(directory) / '.venv-elja' / 'bin' / 'python'
            python.parent.mkdir(parents=True)
            python.touch()
            with patch.object(elja, 'HERE', here), \
                    patch.object(elja.subprocess, 'Popen') as launch:
                elja.launch_node(Path('/job'), 3, 'mimir', 128, 5, StringIO())
            self.assertEqual(launch.call_args.args[0][-6], str(python))

    def test_mixed_slurm_submission_requests_only_selected_resources(self):
        log = StringIO()
        with patch.object(elja.subprocess, 'Popen') as launch:
            elja.launch_node(Path('/job'), 3, 'mimir', 32, 5, log,
                             node_name='compute-66', memory_mib=1600)
        launch.assert_called_once_with([
            'salloc', '--immediate=5', '--nodelist=compute-66', '--mem=1600M',
            '--partition=mimir', '--nodes=1', '--ntasks=1',
            '--cpus-per-task=32', '--job-name=parsim-003',
            sys.executable, str(elja.HERE / 'worker.py'),
            '--job-dir', '/job', '--node-id', '3',
        ], stdin=subprocess.DEVNULL, stdout=log, stderr=log,
            start_new_session=True)

    def test_availability_counts_only_eligible_idle_nodes_once(self):
        with patch.object(elja.subprocess, 'run') as query:
            query.return_value.stdout = (
                'node1|idle|128\nnode1|idle|128\nnode2|mix|128\n'
                'node3|idle*|128\nnode4|idle|64\nnode5|drain|128\n'
                'node6|idle|256\n')
            self.assertEqual(elja.available_node_count('mimir', 128), 2)
        query.assert_called_once_with(
            ['sinfo', '-N', '-h', '--partition=mimir', '-o', '%N|%t|%c'],
            check=True, capture_output=True, text=True)

    def test_availability_empty_partition(self):
        with patch.object(elja.subprocess, 'run') as query:
            query.return_value.stdout = ''
            self.assertEqual(elja.available_node_count('mimir', 128), 0)

    def test_availability_inquiry_errors_are_reported(self):
        for error in (FileNotFoundError('sinfo'),
                      subprocess.CalledProcessError(1, ['sinfo'])):
            with self.subTest(error=error), \
                    patch.object(elja.subprocess, 'run', side_effect=error):
                with self.assertRaisesRegex(RuntimeError, 'Cannot query Slurm'):
                    elja.available_node_count('mimir', 128)
        with patch.object(elja.subprocess, 'run') as query:
            query.return_value.stdout = 'unexpected output'
            with self.assertRaisesRegex(ValueError, 'Unexpected sinfo row'):
                elja.available_node_count('mimir', 128)

    def test_mixed_candidates_filter_memory_and_sort_by_free_cpus(self):
        partitions = [
            {'partition': 'first', 'speed_per_core': 1.0},
            {'partition': 'second', 'speed_per_core': 0.8},
        ]

        def node(name, free_cpus, free_memory, *, partition='first',
                 state=None, threads=2):
            return {
                'name': name, 'state': state or ['MIXED'], 'threads': threads,
                'partitions': ['any_cpu', partition],
                'effective_cpus': 128, 'alloc_cpus': 128 - free_cpus,
                'real_memory': 252000,
                'alloc_memory': 252000 - free_memory,
            }

        records = [
            node('low-memory', 128, 6399),
            node('small', 64, 3200),
            node('largest', 96, 4800, partition='second'),
            node('same-cpus', 96, 4800),
            node('one-thread', 64, 3200, threads=1),
            node('not-mixed', 128, 6400, state=['IDLE']),
        ]
        with patch.object(elja.subprocess, 'run') as query:
            query.return_value.stdout = json.dumps({'nodes': records})
            candidates = elja.available_mixed_nodes(partitions, core_cap=16)
        query.assert_called_once_with(
            ['scontrol', 'show', 'node', '--json'],
            check=True, capture_output=True, text=True)
        self.assertEqual([node['node_name'] for node in candidates],
                         ['same-cpus', 'largest', 'small'])
        self.assertEqual([node['cores'] for node in candidates], [16, 16, 16])
        self.assertEqual([node['slurm_cpus'] for node in candidates],
                         [32, 32, 32])
        self.assertEqual([node['memory_mib'] for node in candidates],
                         [1600, 1600, 1600])
        self.assertEqual([node['speed_per_core'] for node in candidates],
                         [0.6, 0.8 * 0.6, 0.6])
        self.assertEqual(split_counts(160, [
            {'cores': 40, 'speed_per_core': 1.0},
            {'cores': 40, 'speed_per_core': candidates[0]['speed_per_core']},
        ]), [100, 60])

    def test_worker_passes_range_seed_and_core_count_to_sim(self):
        with TemporaryDirectory() as directory:
            job = Path(directory)
            (job / 'assignment-003.json').write_text(json.dumps({
                'start': 37, 'replicates': 19, 'cores': 64,
                'slurm_cpus': 128, 'seed': 1234,
            }))
            with patch.dict(os.environ, {'SLURM_JOB_ID': '5678'}), \
                    patch.object(worker.subprocess, 'run') as run:
                run.return_value.returncode = 0
                self.assertEqual(worker.run_allocated(job, 3), 0)
            run.assert_called_once_with([
                'srun', '--nodes=1', '--ntasks=1',
                '--cpus-per-task=128', '--exact',
                sys.executable, str(worker.BACKEND / 'sim.py'),
                '-a', str(job / 'inputs.json'), '-r', '19', '-i', '37',
                '-C', '64', '-S', '1234',
                '-O', str(job / 'node-003.json'),
                '--progress', str(job / 'progress-003.json'),
            ], check=False)
            ready = json.loads((job / 'allocation-003.json').read_text())
            self.assertEqual(ready, {'node_id': 3, 'slurm_job_id': '5678'})

    def test_dash_seed_clears_saved_seed_before_master_chooses_one(self):
        settings = SimulationSettings()
        settings['random_seed'] = 77
        _, _, prepared = prepare_inputs(
            load_votes(VOTES), [ElectionSystem()], settings,
            {'random_seed': None})
        self.assertIsNone(prepared['random_seed'])

    def run_with_allocations(self, directory, outcomes, *, target_nodes=2,
                             live_processes=(), availability=(3, 3),
                             mixed_nodes=0, mixed_candidates=(), event_order=None,
                             excel_path=None):
        """Exercise the master without starting processes or allocating nodes."""
        job = Path(directory) / 'job'
        processes = [Mock(pid=1000 + i) for i in range(len(outcomes))]
        for i, process in enumerate(processes):
            process.poll.return_value = None if i in live_processes else 0
            process.wait.return_value = 0
        partitions = [
            {'partition': 'first', 'total_nodes': 3, 'cores_per_node': 64,
             'speed_per_core': 1},
            {'partition': 'second', 'total_nodes': 3, 'cores_per_node': 48,
             'speed_per_core': 0.5},
        ]
        settings = {'simulation_count': 17, 'random_seed': 1234}

        def result_for(path):
            assignment = json.loads(path.with_name(
                path.name.replace('node-', 'assignment-')).read_text())
            return {'start_iteration': assignment['start'],
                    'next_global_iteration': (assignment['start']
                                              + assignment['replicates']),
                    'iteration': assignment['replicates'],
                    'random_seed': assignment['seed']}

        with ExitStack() as stack:
            stack.enter_context(redirect_stdout(StringIO()))
            stack.enter_context(patch.object(
                elja, 'available_node_count', side_effect=availability))
            stack.enter_context(patch.object(
                elja, 'available_mixed_nodes', return_value=mixed_candidates))
            launch = stack.enter_context(patch.object(
                elja, 'launch_node', side_effect=processes))
            wait_ready = stack.enter_context(patch.object(
                elja, 'wait_ready', side_effect=outcomes))
            events = Mock()
            events.attach_mock(launch, 'launch')
            events.attach_mock(wait_ready, 'ready')
            read = stack.enter_context(patch(
                'simulation_chunks.read_chunk_result', side_effect=result_for))
            merge = stack.enter_context(patch('simulation_chunks.combine_chunks'))
            write = stack.enter_context(patch('sim.write_csv'))
            kill = stack.enter_context(patch.object(elja.os, 'killpg'))
            try:
                elja.run_distributed(
                    {}, [], settings, csv_path=Path(directory) / 'report.csv',
                    stat_path=None, job_dir=job, partitions=partitions,
                    excel_path=excel_path,
                    target_nodes=target_nodes, first_replicate=37,
                    core_cap=40, immediate=5, mixed_nodes=mixed_nodes)
                if availability[0] >= 2 and mixed_nodes == 0:
                    self.assertEqual(
                        [call[0] for call in events.mock_calls[:3]],
                        ['launch', 'launch', 'ready'])
            except RuntimeError as error:
                if event_order is not None:
                    event_order.extend(call[0] for call in events.mock_calls)
                return job, processes, launch, read, merge, write, kill, error
            if event_order is not None:
                event_order.extend(call[0] for call in events.mock_calls)
        return job, processes, launch, read, merge, write, kill, None

    def test_csv_and_excel_use_the_same_merged_result(self):
        with TemporaryDirectory() as directory, \
                patch('excel_util.simulation_to_xlsx') as export:
            path = Path(directory) / 'results.xlsx'
            _, _, _, read, merge, write, _, error = self.run_with_allocations(
                directory, [{'node_id': 0, 'slurm_job_id': '10'},
                            {'node_id': 1, 'slurm_job_id': '11'}], excel_path=path)
            self.assertIsNone(error)
            self.assertEqual(read.call_count, 2)
            merge.assert_called_once()
            combined = merge.return_value
            self.assertIs(write.call_args.args[1], combined)
            combined.get_result_web.assert_called_once_with(False)
            export.assert_called_once_with(combined.get_result_web.return_value,
                str(path), {'fractional_digits': 3, 'percentage_digits': 1})

    def test_stops_allocating_when_enough_nodes_are_ready(self):
        with TemporaryDirectory() as directory:
            job, _, launch, read, merge, write, kill, error = self.run_with_allocations(
                directory, [{'node_id': 0, 'slurm_job_id': '10'},
                            {'node_id': 1, 'slurm_job_id': '11'}])
            self.assertIsNone(error)
            self.assertEqual([call.args[2] for call in launch.call_args_list],
                             ['first', 'first'])
            self.assertEqual(read.call_count, 2)
            merge.assert_called_once()
            write.assert_called_once()
            kill.assert_not_called()
            manifest = json.loads((job / 'manifest.json').read_text())
            self.assertEqual(manifest['seed'], 1234)
            assignments = [json.loads(path.read_text())
                           for path in sorted(job.glob('assignment-*.json'))]
            self.assertEqual([a['seed'] for a in assignments], [1234, 1234])
            self.assertEqual([a['cores'] for a in assignments], [40, 40])
            self.assertEqual([a['slurm_cpus'] for a in assignments], [128, 128])
            self.assertEqual([a['replicates'] for a in assignments], [9, 8])
            self.assertEqual([a['start'] for a in assignments], [37, 46])
            self.assertTrue((job / 'stop').exists())

    def test_refused_allocation_moves_to_next_partition(self):
        with TemporaryDirectory() as directory:
            job, _, launch, _, merge, _, _, error = self.run_with_allocations(
                directory, [None, {'node_id': 1, 'slurm_job_id': '20'},
                            {'node_id': 2, 'slurm_job_id': '21'}])
            self.assertIsNone(error)
            self.assertEqual([call.args[2] for call in launch.call_args_list],
                             ['first', 'first', 'second'])
            self.assertEqual([call.args[1] for call in launch.call_args_list],
                             [0, 1, 2])
            manifest = json.loads((job / 'manifest.json').read_text())
            self.assertEqual([n['partition'] for n in manifest['nodes']],
                             ['first', 'second'])
            merge.assert_called_once()

    def test_requests_follow_current_availability(self):
        for availability, expected in (((0, 2), ['second', 'second']),
                                       ((1, 1), ['first', 'second'])):
            with self.subTest(availability=availability), \
                    TemporaryDirectory() as directory:
                job, _, launch, _, _, _, _, error = self.run_with_allocations(
                    directory, [{'node_id': 0, 'slurm_job_id': '10'},
                                {'node_id': 1, 'slurm_job_id': '11'}],
                    availability=availability)
                self.assertIsNone(error)
                self.assertEqual([call.args[2] for call in launch.call_args_list],
                                 expected)
                manifest = json.loads((job / 'manifest.json').read_text())
                self.assertEqual(sum(n['replicates'] for n in manifest['nodes']), 17)

    def test_no_idle_nodes_means_no_allocation_requests(self):
        with TemporaryDirectory() as directory:
            _, _, launch, _, merge, _, _, error = self.run_with_allocations(
                directory, [], availability=(0, 0))
            self.assertRegex(str(error), 'Started 0 of 2 requested nodes')
            launch.assert_not_called()
            merge.assert_not_called()

    def test_mixed_nodes_retry_refusal(self):
        candidates = [
            {'node_name': 'mixed-a', 'partition': 'second', 'cores': 20,
             'slurm_cpus': 40, 'memory_mib': 2000, 'speed_per_core': 0.5},
            {'node_name': 'mixed-b', 'partition': 'first', 'cores': 16,
             'slurm_cpus': 32, 'memory_mib': 1600, 'speed_per_core': 1.0},
        ]
        with TemporaryDirectory() as directory:
            job, _, launch, _, merge, _, _, error = self.run_with_allocations(
                directory, [{'node_id': 0, 'slurm_job_id': '10'}, None,
                            {'node_id': 2, 'slurm_job_id': '12'}],
                availability=(1, 0), mixed_nodes=1,
                mixed_candidates=candidates)
            self.assertIsNone(error)
            self.assertEqual([call.args[2] for call in launch.call_args_list],
                             ['first', 'second', 'first'])
            self.assertEqual([call.kwargs.get('node_name')
                              for call in launch.call_args_list],
                             [None, 'mixed-a', 'mixed-b'])
            self.assertEqual([call.kwargs.get('memory_mib')
                              for call in launch.call_args_list],
                             [None, 2000, 1600])
            manifest = json.loads((job / 'manifest.json').read_text())
            self.assertEqual([node['id'] for node in manifest['nodes']], [0, 2])
            self.assertEqual(manifest['nodes'][1]['node_name'], 'mixed-b')
            self.assertEqual(manifest['nodes'][1]['cores'], 16)
            self.assertEqual(manifest['nodes'][1]['slurm_cpus'], 32)
            self.assertEqual(manifest['nodes'][1]['memory_mib'], 1600)
            merge.assert_called_once()

    def test_mixed_count_is_reserved_even_when_idle_nodes_are_available(self):
        candidate = {'node_name': 'mixed-a', 'partition': 'first',
                     'cores': 16, 'slurm_cpus': 32, 'memory_mib': 1600,
                     'speed_per_core': 1.0}
        with TemporaryDirectory() as directory:
            job, _, launch, _, _, _, _, error = self.run_with_allocations(
                directory, [{'node_id': 0, 'slurm_job_id': '10'},
                            {'node_id': 1, 'slurm_job_id': '11'}],
                availability=(3, 3), mixed_nodes=1,
                mixed_candidates=[candidate])
            self.assertIsNone(error)
            self.assertEqual([call.kwargs.get('node_name')
                              for call in launch.call_args_list],
                             [None, 'mixed-a'])
            manifest = json.loads((job / 'manifest.json').read_text())
            self.assertEqual([node.get('mode') for node in manifest['nodes']],
                             [None, 'mixed'])

    def test_missing_mixed_node_does_not_consume_extra_idle_node(self):
        with TemporaryDirectory() as directory:
            job, _, launch, _, _, _, _, error = self.run_with_allocations(
                directory, [{'node_id': 0, 'slurm_job_id': '10'}],
                availability=(3, 3), mixed_nodes=1)
            self.assertRegex(str(error), r'1/1 idle, 0/1 mixed')
            self.assertEqual(launch.call_count, 1)
            self.assertFalse((job / 'manifest.json').exists())

    def test_mixed_requests_launch_together_and_retry_failed_batch(self):
        candidates = [
            {'node_name': name, 'partition': 'first', 'cores': 16,
             'slurm_cpus': 32, 'memory_mib': 1600, 'speed_per_core': 1.0}
            for name in ('mixed-a', 'mixed-b', 'mixed-c')
        ]
        with TemporaryDirectory() as directory:
            event_order = []
            job, _, launch, _, _, _, _, error = self.run_with_allocations(
                directory, [None, {'node_id': 1, 'slurm_job_id': '11'},
                            {'node_id': 2, 'slurm_job_id': '12'}],
                availability=(0, 0), mixed_nodes=2,
                mixed_candidates=candidates, event_order=event_order)
            self.assertIsNone(error)
            self.assertEqual(event_order[:6],
                             ['launch', 'launch', 'ready', 'ready',
                              'launch', 'ready'])
            self.assertEqual([call.kwargs['node_name']
                              for call in launch.call_args_list],
                             ['mixed-a', 'mixed-b', 'mixed-c'])
            manifest = json.loads((job / 'manifest.json').read_text())
            self.assertEqual([node['id'] for node in manifest['nodes']], [1, 2])

    def test_exhausted_partitions_release_acquired_allocation(self):
        with TemporaryDirectory() as directory:
            job, processes, launch, read, merge, write, kill, error = (
                self.run_with_allocations(
                    directory, [{'node_id': 0, 'slurm_job_id': '10'}, None, None],
                    live_processes=(0,)))
            self.assertRegex(str(error), 'Started 1 of 2 requested nodes')
            self.assertEqual([call.args[2] for call in launch.call_args_list],
                             ['first', 'first', 'second'])
            kill.assert_called_once_with(processes[0].pid, signal.SIGTERM)
            for process in processes:
                process.wait.assert_any_call(timeout=10)
            self.assertTrue((job / 'stop').exists())
            self.assertFalse((job / 'manifest.json').exists())
            read.assert_not_called()
            merge.assert_not_called()
            write.assert_not_called()

    def test_slurm_launch_protocol_with_stub_commands(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            all_file = base / 'all.json'
            all_file.write_text(json.dumps({
                'vote_table': load_votes(VOTES),
                'systems': [ElectionSystem()],
                'sim_settings': dict(SimulationSettings(), sensitivity=True,
                                     sensitivity_covs=[0.01, 0.1],
                                     sensitivity_gen_method='uniform',
                                     sensitivity_simulation_count=2),
                'display_settings': {'fractional_digits': 4, 'percentage_digits': 2},
            }), encoding='utf-8')
            partitions = base / 'partitions.txt'
            partitions.write_text(
                'Nodes\tCores\tMaxNode\tSpeed\tPart\n'
                '2\t2\t1\t1\tbusy\n'
                '2\t2\t2\t1\ttest\n', encoding='utf-8')
            fake_bin = base / 'bin'
            fake_bin.mkdir()
            sinfo = fake_bin / 'sinfo'
            sinfo.write_text(
                '#!/usr/bin/env python3\n'
                'import sys\n'
                'partition = next(arg.split("=", 1)[1] for arg in sys.argv '
                'if arg.startswith("--partition="))\n'
                'print(f"{partition}1|idle|4\\n{partition}2|idle|4")\n',
                encoding='utf-8')
            sinfo.chmod(0o755)
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
                 '--partitions', str(partitions)],
                env={**os.environ, 'PATH': f'{fake_bin}:{os.environ["PATH"]}'},
                capture_output=True, text=True, check=False, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            for filename in ('inputs.json', 'node-002.json', 'node-003.json'):
                saved = (json.loads((job_dir / filename).read_text())
                         if filename == 'inputs.json' else
                         read_chunk_result(job_dir / filename))
                saved_settings = saved['sim_settings']
                self.assertTrue(saved_settings['sensitivity'])
                self.assertEqual(saved_settings['sensitivity_covs'], [0.01, 0.1])
                self.assertEqual(saved_settings['sensitivity_gen_method'], 'uniform')
                self.assertEqual(saved_settings['sensitivity_simulation_count'], 2)
            self.assertTrue(output.exists())
            ready = json.loads((job_dir / 'allocation-002.json').read_text())
            self.assertEqual(ready['slurm_job_id'], '12345')
            manifest = json.loads((job_dir / 'manifest.json').read_text())
            self.assertEqual([node['partition'] for node in manifest['nodes']],
                             ['test', 'test'])
            self.assertEqual([node['cores'] for node in manifest['nodes']],
                             [2, 2])
            self.assertEqual([node['slurm_cpus'] for node in manifest['nodes']],
                             [4, 4])
            for node in manifest['nodes']:
                progress = json.loads((job_dir / f"progress-{node['id']:03d}.json").read_text())
                self.assertEqual(progress['completed'], node['replicates'])
                self.assertEqual(progress['assigned'], node['replicates'])
            self.assertIn('remaining', completed.stdout)
            self.assertIn('100.0%', completed.stdout)
            frozen = json.loads((job_dir / 'inputs.json').read_text())
            self.assertEqual(frozen['display_settings'],
                             {'fractional_digits': 4, 'percentage_digits': 2})
            from sim import main as sim_main
            direct = base / 'direct.csv'
            self.assertEqual(sim_main(['-a', str(all_file), '-r', '4', '-S', '123',
                                       '-C', '2', '-o', str(direct)]), 0)
            self.assertEqual(output.read_bytes(), direct.read_bytes())


if __name__ == '__main__':
    unittest.main()
