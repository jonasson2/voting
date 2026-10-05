from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from parsim.elja import wait_for_nodes
from simulation_progress import ProgressDisplay, ReplicateMonitor, write_progress


class SimulationProgressTest(unittest.TestCase):
    def test_cpu_counts_are_throttled_and_final_count_is_always_reported(self):
        counts = [0, 0]
        monitor = ReplicateMonitor(counts, [4, 4])
        with patch('simulation_progress.time.monotonic', side_effect=[20, 21, 35, 36]):
            monitor.monitor(1, 1)
            self.assertEqual(counts, [0, 1])
            monitor.monitor(1, 2)
            self.assertEqual(counts, [0, 1])
            monitor.monitor(1, 3)
            self.assertEqual(counts, [0, 3])
            monitor.monitor(1, 4)
            self.assertEqual(counts, [0, 4])

    def test_node_file_contains_aggregated_counts(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'progress.json'
            with patch('simulation_progress.time.monotonic', return_value=25):
                write_progress(path, [4, 3], 10, 5)
            self.assertEqual(json.loads(path.read_text()),
                             {'completed': 7, 'assigned': 10, 'elapsed': 20})
            self.assertFalse(path.with_suffix('.json.tmp').exists())

    def test_remaining_uses_slowest_node_and_recent_rate(self):
        nodes = [{'id': 0, 'replicates': 100}, {'id': 1, 'replicates': 100}]
        display = ProgressDisplay()
        line = display.line(nodes, {
            0: {'completed': 50, 'elapsed': 10},
            1: {'completed': 10, 'elapsed': 10},
        }, set(), 10)
        self.assertIn('Completed 60 / 200 (30.0%)', line)
        self.assertIn('remaining 1m 30s', line)
        line = display.line(nodes, {
            0: {'completed': 90, 'elapsed': 20},
            1: {'completed': 50, 'elapsed': 20},
        }, set(), 20)
        self.assertIn('remaining 12s', line)
        self.assertNotIn('ETA', line)

    def test_unknown_progress_and_finished_nodes(self):
        nodes = [{'id': 0, 'replicates': 10}]
        display = ProgressDisplay()
        self.assertIn('remaining --', display.line(nodes, {}, set(), 0))
        line = display.line(nodes, {}, {0}, 5)
        self.assertIn('Completed 10 / 10 (100.0%)', line)
        self.assertIn('1 nodes, 1 finished', line)
        self.assertIn('remaining 0s', line)

    def test_master_polls_progress_and_node_completion(self):
        with TemporaryDirectory() as directory:
            job = Path(directory)
            (job / 'progress-000.json').write_text(json.dumps(
                {'completed': 2, 'assigned': 4, 'elapsed': 1}))
            process = Mock()
            process.poll.side_effect = [None, 0]
            output = StringIO()
            with redirect_stdout(output), patch('parsim.elja.time.sleep') as sleep:
                wait_for_nodes([(0, process, '/job/attempt.log')],
                               [{'id': 0, 'replicates': 4}], job)
            sleep.assert_called_once_with(0.2)
            self.assertIn('(50.0%)', output.getvalue())
            self.assertIn('(100.0%)', output.getvalue())

    def test_master_reports_worker_failure(self):
        process = Mock()
        process.poll.return_value = 1
        with TemporaryDirectory() as directory, redirect_stdout(StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'Node 0 failed; inspect /job/log'):
                wait_for_nodes([(0, process, '/job/log')],
                               [{'id': 0, 'replicates': 4}], Path(directory))
