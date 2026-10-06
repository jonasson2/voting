from types import SimpleNamespace
import unittest

import numpy as np

from voting import Election


class VotesPerSeatTest(unittest.TestCase):
    def test_final_seats_pruned_votes_and_constituency_total(self):
        election = Election.__new__(Election)
        election.system = {'special_rules': ''}
        election.votes = np.array([[120, 80], [50, 50], [0, 0]])
        election.pruned_votes = np.array([40, 0, 0])
        election.results = {
            'all_const_seats': [[2, 1], [1, 0], [0, 0]],
            'all': [[2, 1, 3], [1, 0, 1], [0, 0, 0], [3, 1, 4]],
            'adj': [[0, 1, 1], [0, 0, 0], [0, 0, 0], [0, 1, 1]],
        }
        election.demo_tables = []
        election.tie_report = SimpleNamespace(events=[])
        self.assertEqual(election.get_result_web()['votes_per_seat'],
                         [80.0, 100.0, None, 85.0])
