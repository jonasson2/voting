"""Independent checks against exhaustive feasible allocations and the displayed E."""

from itertools import permutations, product
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from division_rules import dhondt_gen, sainte_lague_gen, danish_gen
from dictionaries import DIVIDER_RULES
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from noweb import load_votes
from methods.seat_share import exact, switching, improve_by_exchanges
from reference_measures import dhondt_objective, list_measures
from simulate import SimulationSettings
from simulation_chunks import run_chunk, combine_chunks


class SeatShareTest(unittest.TestCase):
    def test_other_rules_minimize_their_own_cumulative_divisor_cost(self):
        votes = np.array([[40, 25], [41, 83]])
        reference = self.reference(votes, [2, 4])
        feasible = [np.array([[a, 2-a], [3-a, 1+a]]) for a in range(3)]
        formulae = (
            (dhondt_gen, lambda s: s * (s + 1) / 2),
            (sainte_lague_gen, lambda s: s ** 2),
            (danish_gen, lambda s: (3 * s ** 2 - s) / 2),
        )
        allocations = []
        for rule, cumulative in formulae:
            with self.subTest(rule=rule.__name__):
                allocation, _ = exact(votes, [2, 4], [3, 3], np.zeros((2, 2), int), rule)
                allocations.append(allocation)
                value = lambda a: float((cumulative(a) / reference).sum())
                self.assertAlmostEqual(value(allocation), min(value(a) for a in feasible))
                if rule is dhondt_gen:
                    self.assertAlmostEqual(dhondt_objective(allocation, reference),
                                           min(value(a) for a in feasible))
                approx, _ = switching(votes, [2, 4], [3, 3], np.zeros((2, 2), int), rule)
                self.assertAlmostEqual(value(approx), value(allocation))
        self.assertFalse(np.array_equal(allocations[0], allocations[1]))

    def test_all_selectable_divisor_rules_are_accepted(self):
        for name, rule in DIVIDER_RULES.items():
            for method in (exact, switching):
                with self.subTest(rule=name, method=method.__name__):
                    allocation, _ = method([[100, 30], [20, 90]], [2, 2], [2, 2],
                                           [[0, 0], [0, 0]], rule)
                    np.testing.assert_array_equal(allocation.sum(0), [2, 2])
                    np.testing.assert_array_equal(allocation.sum(1), [2, 2])

    @staticmethod
    def systems(table, rule="sainte-lague"):
        systems = []
        for method in ("seat-share-lp", "seat-share-switching"):
            system = ElectionSystem()
            system.copy_info_from_votes(table)
            system.update(name=method, adjustment_method=method, adj_alloc_divider=rule)
            systems.append(system)
        return systems

    def test_election_simulation_and_report_exports_preserve_the_selected_rule(self):
        from sim import write_csv
        from excel_util import simulation_to_xlsx
        from input_files import load_systems
        import json
        import openpyxl
        table = load_votes("../data/2-by-2-example.csv")
        table["votes"] = [[40, 25], [41, 83]]
        for constituency, seats in zip(table["constituencies"], [2, 4]):
            constituency.update(num_fixed_seats=0, num_adj_seats=seats)
        for rule, expected in (("dhondt", [[2, 0], [1, 3]]),
                               ("sainte-lague", [[1, 1], [2, 2]])):
            systems = self.systems(table, rule)
            handler = ElectionHandler(table, deepcopy(systems), True)
            for election in handler.elections:
                self.assertEqual(election.system["adj_alloc_divider"], rule)
                np.testing.assert_array_equal(election.results["all_const_seats"], expected)
                for demo in election.demo_tables:
                    self.assertTrue(all(len(row) == len(demo["headers"]) for row in demo["steps"]))
            settings = SimulationSettings()
            settings.update(simulation_count=3, cpu_count=1, random_seed=123,
                            sensitivity=True, sensitivity_simulation_count=2,
                            sensitivity_covs=[.1], single_list_sensitivity=True,
                            single_list_simulation_count=2)
            result = combine_chunks([run_chunk(table, systems, settings, 3, 0)])
            self.assertTrue(all(np.isfinite(system["local_squared"]["avg"])
                                for system in result.data))
            with TemporaryDirectory() as directory:
                folder = Path(directory)
                saved = folder / "systems.json"
                saved.write_text(json.dumps({"systems": systems}))
                imported = load_systems(saved)
                self.assertEqual([system["adj_alloc_divider"] for system in imported], [rule] * 2)
                write_csv(folder / "results.csv", result)
                self.assertIn("Local squared deviation per reference seat", (folder / "results.csv").read_text())
                self.assertNotIn("Generalized D'Hondt objective",
                                 (folder / "results.csv").read_text())
                result.sim_settings['show_additional'] = True
                write_csv(folder / "results.csv", result)
                self.assertIn("Generalized D'Hondt objective",
                              (folder / "results.csv").read_text())
                simulation_to_xlsx(result.get_result_web(False), str(folder / "results.xlsx"))
                workbook = openpyxl.load_workbook(folder / "results.xlsx")
                self.assertIn("Quality measures", workbook.sheetnames)
                self.assertIn("Generalized D'Hondt objective", [
                    cell.value for row in workbook['Quality measures'] for cell in row])
                workbook.close()

    def test_reported_dhondt_objective_includes_fixed_seats_and_handles_zero_lists(self):
        self.assertEqual(dhondt_objective([[2, 0], [0, 2]], [[1, 1], [1, 1]]), 6)
        self.assertEqual(dhondt_objective([[0, 1]], [[0, 2]]), .5)
        self.assertEqual(dhondt_objective([[1, 0]], [[0, 2]]), float('inf'))
        table = load_votes('../data/2-by-2-example.csv')
        systems = self.systems(table, 'dhondt')
        elections = ElectionHandler(table, deepcopy(systems), True).elections
        settings = dict(SimulationSettings(), simulation_count=2, cpu_count=1,
                        random_seed=123, const_rsd=0, sensitivity=False)
        result = combine_chunks([run_chunk(table, systems, settings, 2, 0)])
        for election, data in zip(elections, result.data):
            seats = np.asarray(election.results['all_const_seats'])
            q = election.reference_seats('const')
            expected = sum(sum(range(1, int(s) + 1)) / fair
                           for s, fair in zip(seats.flat, q.flat))
            self.assertAlmostEqual(data['local_dhondt']['avg'], expected)
            self.assertEqual(data['local_dhondt']['std'], 0)

    def test_election_handler_rejects_flexible_pool(self):
        table = load_votes("../data/2-by-2-example.csv")
        for system in self.systems(table):
            system["seat_spec_options"]["const"] = "flexible"
            with self.assertRaisesRegex(ValueError, "predetermined final seat count"):
                ElectionHandler(table, [system], True)

    def test_methods_honor_region_constraints(self):
        import csv
        from vote_table import check_vote_table, process_vote_table
        rows = csv.reader([
            "Example,fixed,adj,region,A,B",
            "North 1,2,1,N,70,30", "South 1,3,1,S,60,40",
            "North 2,1,1,N,20,80", "South 2,1,1,S,30,70",
            ",,,,,", "Regions,Name,adj,,,",
            "N,North,2,,,", "S,South,2,,,",
        ])
        table = check_vote_table(process_vote_table(list(rows), "test.csv"))
        for election in ElectionHandler(table, self.systems(table), True).elections:
            allocation = np.asarray(election.results["all_const_seats"])
            for group, totals in zip(election.region_groups, election.region_party_totals):
                np.testing.assert_array_equal(allocation[group].sum(0), totals)

    @staticmethod
    def reference(votes, rows):
        votes = np.asarray(votes, dtype=float)
        totals = votes.sum(axis=1)[:, None]
        return np.divide(votes, totals, out=np.zeros_like(votes), where=totals > 0) * np.asarray(rows)[:, None]

    @classmethod
    def error(cls, votes, rows, allocation):
        return list_measures(allocation, cls.reference(votes, rows))["relative_squared"]

    def test_exact_minimizes_displayed_measure_over_all_feasible_allocations(self):
        cases = [
            ([[100, 30], [20, 90]], [2, 3], [3, 2], [[1, 0], [0, 1]]),
            ([[.03, .07], [.09, .01]], [1, 3], [2, 2], [[0, 0], [0, 0]]),
            ([[7, 13], [2, 1]], [3, 2], [2, 3], [[0, 1], [1, 0]]),
        ]
        for votes, rows, parties, prior in cases:
            with self.subTest(votes=votes):
                prior = np.asarray(prior)
                feasible = []
                for a, b in product(range(rows[0] + 1), range(rows[1] + 1)):
                    candidate = np.array([[a, rows[0] - a], [b, rows[1] - b]])
                    if (candidate >= prior).all() and np.array_equal(candidate.sum(0), parties):
                        feasible.append(candidate)
                optimum = min(self.error(votes, rows, candidate) for candidate in feasible)
                allocation, _ = exact(votes, rows, parties, prior)
                self.assertAlmostEqual(self.error(votes, rows, allocation), optimum)
                np.testing.assert_array_equal(allocation.sum(0), parties)
                np.testing.assert_array_equal(allocation.sum(1), rows)
                self.assertTrue((allocation >= prior).all())

    def test_exact_assignment_matches_exhaustive_three_constituency_search(self):
        rng = np.random.default_rng(521)
        for _ in range(30):
            votes = rng.uniform(.001, 10, (3, 3))
            candidates = [np.eye(3, dtype=int)[list(order)] for order in permutations(range(3))]
            allocation, _ = exact(votes, [1] * 3, [1] * 3, np.zeros((3, 3), int))
            self.assertAlmostEqual(self.error(votes, [1] * 3, allocation),
                                   min(self.error(votes, [1] * 3, a) for a in candidates))

    def test_uses_constituency_vote_shares_and_keeps_fractional_votes(self):
        votes = np.array([[.03, .07], [.09, .01]])
        for method in (exact, switching):
            original, _ = method(votes, [1, 3], [2, 2], np.zeros((2, 2), int))
            rescaled, _ = method(votes * np.array([[1e4], [1e-4]]), [1, 3], [2, 2],
                                 np.zeros((2, 2), int))
            np.testing.assert_array_equal(original, rescaled)
            self.assertLessEqual(self.error(votes, [1, 3], original),
                                self.error(votes, [1, 3], [[0, 1], [2, 1]]))

    def test_switching_improvements_reduce_E_and_preserve_both_margins(self):
        reference = np.array([[.2, .8], [.7, .3]])
        start = np.eye(2, dtype=int)
        allocation, exchanges = improve_by_exchanges(reference, start, np.zeros((2, 2), int))
        np.testing.assert_array_equal(allocation, [[0, 1], [1, 0]])
        reduction = list_measures(start, reference)["relative_squared"] - list_measures(allocation, reference)["relative_squared"]
        self.assertAlmostEqual(exchanges[0]["reduction"], reduction)
        self.assertGreater(reduction, 0)

    def test_switching_stops_at_pairwise_optimum_and_respects_protected_seats(self):
        rng = np.random.default_rng(218)
        for _ in range(20):
            votes = rng.uniform(.01, 10, (3, 3))
            prior = np.eye(3, dtype=int)
            allocation, demo = switching(votes, [3] * 3, [3] * 3, prior)
            np.testing.assert_array_equal(allocation.sum(0), [3] * 3)
            np.testing.assert_array_equal(allocation.sum(1), [3] * 3)
            self.assertTrue((allocation >= prior).all())
            value = self.error(votes, [3] * 3, allocation)
            optimum, _ = exact(votes, [3] * 3, [3] * 3, prior)
            self.assertGreaterEqual(value + 1e-9, self.error(votes, [3] * 3, optimum))
            for c, d, p, q in product(range(3), repeat=4):
                if c == d or p == q or allocation[c, p] <= prior[c, p] or allocation[d, q] <= prior[d, q]:
                    continue
                candidate = allocation.copy()
                candidate[c, p] -= 1; candidate[d, p] += 1
                candidate[d, q] -= 1; candidate[c, q] += 1
                self.assertGreaterEqual(self.error(votes, [3] * 3, candidate) + 1e-9, value)
            for printer in demo["functions"]:
                headers, rows, _ = printer({"constituencies": [{"name": str(i)} for i in range(3)],
                                          "parties": ["A", "B", "C"]}, demo["data"])
                self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_pairwise_switching_can_miss_a_three_constituency_cycle(self):
        votes = np.array([[3, 6, 1], [1, 3, 6], [6, 1, 3]])
        reference = self.reference(votes, [1] * 3)
        local, exchanges = improve_by_exchanges(reference, np.eye(3, dtype=int), np.zeros((3, 3), int))
        optimum, _ = exact(votes, [1] * 3, [1] * 3, np.zeros((3, 3), int))
        self.assertEqual(exchanges, [])
        self.assertGreater(self.error(votes, [1] * 3, local), self.error(votes, [1] * 3, optimum))

    def test_sparse_votes_use_a_feasible_start_instead_of_greedy_dead_end(self):
        votes = np.array([[6, 4, 0], [6, 4, 0], [7, 0, 3]])
        allocation, demo = switching(votes, [1] * 3, [1] * 3, np.zeros((3, 3), int))
        self.assertIsNone(demo["data"]["initial"])
        np.testing.assert_array_equal(allocation.sum(0), [1] * 3)
        np.testing.assert_array_equal(allocation.sum(1), [1] * 3)
        self.assertTrue((allocation[votes == 0] == 0).all())

    def test_zero_votes_and_zero_seat_constituencies(self):
        for method in (exact, switching):
            allocation, _ = method([[0, 0], [0, 30]], [0, 2], [0, 2], np.zeros((2, 2), int))
            np.testing.assert_array_equal(allocation, [[0, 0], [0, 2]])
            with self.assertRaises(ValueError):
                method([[100, 0]], [1], [0, 1], [[0, 0]])
            with self.assertRaisesRegex(ValueError, "zero-vote"):
                method([[0, 100]], [2], [1, 1], [[1, 0]])
            with self.assertRaisesRegex(ValueError, "fixed constituency"):
                method([[100, 50]], [0], [1, 1], [[0, 0]], num_adjustment_seats=2,
                       min_adj_seats=[0], max_adj_seats=[None])

    def test_no_adjustment_seats_keep_protected_allocation(self):
        for method in (exact, switching):
            allocation, _ = method([[70, 30]], [2], [1, 1], [[1, 1]], dhondt_gen)
            np.testing.assert_array_equal(allocation, [[1, 1]])
