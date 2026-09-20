from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import numpy as np
from openpyxl import load_workbook

from division_rules import dhondt_gen
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from methods.common_methods import max_const_vote_percentage
from methods.max_const_votes import max_const_votes
from noweb import load_votes
from randomness import make_rng
from simulate import Simulation, SimulationSettings


class FlexibleAllocationTest(unittest.TestCase):
    def allocate(self, method=max_const_votes, **options):
        settings = dict(num_adjustment_seats=2, min_adj_seats=[1, 0],
                        max_adj_seats=[None, None])
        settings.update(options)
        return method([[10, 9], [100, 10]], [1, 0], [1, 1],
                      np.zeros((2, 2), int), dhondt_gen, **settings)

    def test_minima_are_filled_before_the_remaining_pool(self):
        allocation, demo = self.allocate()
        # The old reserve-minima-until-needed algorithm gave A to row 2 first.
        np.testing.assert_array_equal(allocation, [[1, 0], [0, 1]])
        steps = demo["data"]
        self.assertEqual([(s["constituency"], s["party"], s["phase"]) for s in steps],
                         [(0, 0, "minimum"), (1, 1, "flexible")])

    def test_finite_maximum_is_binding_and_includes_the_minimum_pass(self):
        allocation, demo = max_const_votes(
            [[100, 1], [10, 9]], [3, 1], [4, 2], [[2, 0], [0, 1]], dhondt_gen,
            num_adjustment_seats=3, min_adj_seats=[1, 0], max_adj_seats=[1, None])
        np.testing.assert_array_equal(allocation, [[3, 0], [1, 2]])
        self.assertEqual([s["constituency"] for s in demo["data"]], [0, 1, 1])
        self.assertEqual([s["divisor"] for s in demo["data"]], [3, 1, 2])

    def test_vote_percentage_uses_its_own_criterion_in_both_passes(self):
        votes = [[10, 9], [100, 10]]
        options = dict(num_adjustment_seats=2, min_adj_seats=[1, 0],
                       max_adj_seats=[None, None])
        allocation, demo = max_const_vote_percentage(
            votes, [1, 0], [1, 1], np.zeros((2, 2), int), dhondt_gen, **options)
        np.testing.assert_array_equal(allocation, [[1, 1], [0, 0]])
        self.assertAlmostEqual(demo["data"]["sequence"][1]["maximum"], 9 / 19)
        np.testing.assert_array_equal(votes, [[10, 9], [100, 10]])

    def test_exact_bounds_skip_the_flexible_pass(self):
        with patch("allocate_pool.allocate_pool") as flexible:
            allocation, demo = self.allocate(min_adj_seats=[1, 1], max_adj_seats=[1, 1])
        flexible.assert_not_called()
        np.testing.assert_array_equal(allocation.sum(axis=1), [1, 1])
        self.assertTrue(all(s["phase"] == "minimum" for s in demo["data"]))

    def test_unlimited_bounds_with_total_equal_to_minima_skip_second_pass(self):
        allocation, _ = self.allocate(min_adj_seats=[1, 1])
        np.testing.assert_array_equal(allocation.sum(axis=1), [1, 1])

    def test_zero_pool_and_zero_minima_leave_prior_allocations_alone(self):
        for method in (max_const_votes, max_const_vote_percentage):
            allocation, _ = method([[100, 1]], [2], [2, 0], [[2, 0]], dhondt_gen,
                                   num_adjustment_seats=0, min_adj_seats=[0], max_adj_seats=[None])
            np.testing.assert_array_equal(allocation, [[2, 0]])

    def test_raw_votes_and_generic_vote_floor_remain_distinct(self):
        votes = np.array([[0.2, 0.8]])
        original = votes.copy()
        for method, expected in [(max_const_votes, [[0, 1]]),
                                 (max_const_vote_percentage, [[1, 0]])]:
            for minimum in (0, 1):
                allocation, _ = method(votes, [minimum], [1, 1], [[0, 0]], dhondt_gen,
                    num_adjustment_seats=1, min_adj_seats=[minimum], max_adj_seats=[None])
                np.testing.assert_array_equal(allocation, expected)
                np.testing.assert_array_equal(votes, original)

    def test_national_fixed_seats_are_subtracted_once(self):
        for method in (max_const_votes, max_const_vote_percentage):
            allocation, _ = method(
                [[100, 2], [9, 8]], [1, 0], [2, 2], np.zeros((2, 2), int), dhondt_gen,
                num_adjustment_seats=3, min_adj_seats=[1, 0], max_adj_seats=[1, None],
                nat_prior_allocations=[1, 0])
            np.testing.assert_array_equal(allocation, [[1, 0], [0, 2]])

    def test_remaining_national_adjustment_seats_do_not_extend_the_pool(self):
        allocation, demo = max_const_votes(
            [[100, 2]], [0], [3, 3], [[0, 0]], dhondt_gen,
            num_adjustment_seats=1, min_adj_seats=[0], max_adj_seats=[None],
            nat_prior_allocations=[1, 1])
        np.testing.assert_array_equal(allocation, [[1, 0]])
        self.assertEqual(len(demo["data"]), 1)

    def test_invalid_bounds_and_party_deficits_fail_clearly(self):
        cases = [
            ({"min_adj_seats": [-1, 0]}, "non-negative"),
            ({"min_adj_seats": [3, 0]}, "minimums exceed"),
            ({"max_adj_seats": [0, None]}, "maximum is below"),
            ({"max_adj_seats": [1, 0]}, "maxima prevent"),
            ({"num_adjustment_seats": 3}, "Party deficits"),
            ({"max_adj_seats": [1]}, "do not match"),
            ({"nat_prior_allocations": [2, 0]}, "party excess"),
        ]
        for options, message in cases:
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, message):
                self.allocate(**options)

    def test_zero_vote_exclusion_can_fail_in_either_pass(self):
        for minimum in (0, 1):
            with self.subTest(minimum=minimum), self.assertRaisesRegex(ValueError, "No eligible"):
                max_const_votes([[100, 0]], [minimum], [0, 1], [[0, 0]], dhondt_gen,
                    num_adjustment_seats=1, min_adj_seats=[minimum], max_adj_seats=[None],
                    exclude_zero_votes=True)

    def test_all_tied_pairs_are_available_in_both_passes(self):
        for minimums in ([0, 0], [1, 1]):
            report = Mock()
            allocation, demo = max_const_votes(
                [[10, 10], [10, 10]], minimums, [0, 2], [[0, 0], [0, 0]], dhondt_gen,
                num_adjustment_seats=2, min_adj_seats=minimums, max_adj_seats=[None, None],
                on_tie=report)
            np.testing.assert_array_equal(report.call_args_list[0].args[0], [1, 3])
            self.assertEqual(demo["data"][0]["constituency"], 0)
            self.assertTrue(demo["data"][0]["tie"])
            self.assertEqual(int(allocation.sum()), 2)

        for minimums in ([0, 0], [1, 1]):
            report = Mock()
            with patch("ties.random_index", side_effect=lambda rng, size: size - 1):
                _, demo = max_const_votes(
                    [[10, 10], [10, 10]], minimums, [1, 1], [[0, 0], [0, 0]], dhondt_gen,
                    num_adjustment_seats=2, min_adj_seats=minimums, max_adj_seats=[None, None],
                    rng=make_rng(42), on_tie=report)
            np.testing.assert_array_equal(report.call_args_list[0].args[0], [0, 1, 2, 3])
            self.assertEqual((demo["data"][0]["constituency"], demo["data"][0]["party"]), (1, 1))
            self.assertTrue(demo["data"][0]["lot"])

    def table_and_system(self, method="max-const-vote-percentage"):
        table = load_votes("../data/2-by-2-example.csv")
        table["constituencies"][0].update(num_adj_seats=1, max_adj_seats=1)
        table["constituencies"][1].update(num_adj_seats=0, max_adj_seats=None)
        table["max_total_adj_seats"] = 4
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        system["adjustment_method"] = method
        return table, system

    def test_single_election_step_table_and_excel_show_both_passes(self):
        for method in ("max-const-votes", "max-const-vote-percentage"):
            table, system = self.table_and_system(method)
            handler = ElectionHandler(table, [system], True)
            election = handler.elections[0]
            np.testing.assert_array_equal(np.asarray(election.results["adj_const_seats"]).sum(axis=1), [1, 3])
            demo = election.demo_tables[0]
            self.assertEqual([s[0] for s in demo["steps"]], [1, 2, 3, 4])
            self.assertIn("Constituency minimum", demo["steps"][0][3])
            self.assertTrue(all("Remaining pool" in s[3] for s in demo["steps"][1:]))
            with TemporaryDirectory() as directory:
                path = Path(directory) / "election.xlsx"
                handler.to_xlsx(path)
                book = load_workbook(path)
                text = [cell.value for sheet in book for row in sheet for cell in row]
                self.assertIn(demo["steps"][0][3], text)
                self.assertIn(demo["steps"][1][3], text)
                book.close()

    def test_unsupported_method_accepts_an_empty_flexible_pass(self):
        table, system = self.table_and_system("max-const-seat-share")
        table["max_total_adj_seats"] = 1
        election = ElectionHandler(table, [system], True).elections[0]
        np.testing.assert_array_equal(np.asarray(election.results["adj_const_seats"]).sum(axis=1), [1, 0])

    def test_simulation_observes_bounds_and_is_reproducible(self):
        table, system = self.table_and_system()
        settings = SimulationSettings()
        settings.update(simulation_count=3, cpu_count=1, random_seed=123)
        runs = []
        for _ in range(2):
            simulation = Simulation(settings, [system], deepcopy(table))
            simulation.simulate()
            election = simulation.election_handler.elections[0]
            np.testing.assert_array_equal(np.asarray(election.results["adj_const_seats"]).sum(axis=1), [1, 3])
            runs.append(election.results["all_const_seats"])
        np.testing.assert_array_equal(*runs)

    def test_dense_positive_cases_always_finish_within_bounds(self):
        rng = np.random.default_rng(81)
        for method in (max_const_votes, max_const_vote_percentage):
            for _ in range(20):
                prior = rng.integers(0, 3, size=(3, 4))
                witness = rng.integers(0, 4, size=(3, 4))
                rows = witness.sum(axis=1)
                minimums = rows // 2
                maxima = [int(rows[0]), None, int(rows[2] + 2)]
                targets = (prior + witness).sum(axis=0)
                allocation, _ = method(
                    rng.uniform(1, 100, size=(3, 4)), prior.sum(axis=1) + minimums,
                    targets, prior, dhondt_gen, num_adjustment_seats=int(rows.sum()),
                    min_adj_seats=minimums, max_adj_seats=maxima)
                added = (allocation - prior).sum(axis=1)
                self.assertTrue(np.all(allocation >= prior))
                self.assertTrue(np.all(added >= minimums))
                self.assertLessEqual(added[0], maxima[0])
                self.assertLessEqual(added[2], maxima[2])
                np.testing.assert_array_equal(allocation.sum(axis=0), targets)
