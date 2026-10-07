from copy import deepcopy
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
from openpyxl import load_workbook

import entropy_score
from dictionaries import SENS_MEASURES
import noweb
from par_util import write_sim_dict, write_sim_status
from electionSystem import ElectionSystem
from input_util import check_simul_settings
from noweb import load_votes
from sensitivity import (
    generate_perturbations, seat_displacements, sensitivity_covs,
    sensitivity_statistics, single_list_perturbations, single_list_category,
    SINGLE_LIST_MEASURES)
from running_stats import Running_stats
from simulation_excel import SimulationWorkbook
from simulate import Sim_result, Simulation, SimulationSettings
from randomness import make_rng


class SensitivityTest(unittest.TestCase):
    def test_one_seeded_generator_per_replicate_including_sensitivity(self):
        table = load_votes("../data/2-by-2-example.csv")
        simulation = Simulation(
            self.settings(simulation_count=2), [self.make_system(table)],
            table, start_iteration=5)
        with patch("simulate.make_rng", wraps=make_rng) as create:
            simulation.simulate()
        self.assertEqual(
            [record.args for record in create.call_args_list],
            [(123, (5,)), (123, (6,))])

    def make_system(self, table, name="System-1"):
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        system["name"] = name
        system["adjustment_method"] = "max-const-seat-share"
        return system

    def settings(self, **updates):
        settings = SimulationSettings()
        settings.update({
            "simulation_count": 2,
            "cpu_count": 1,
            "random_seed": 123,
            "sensitivity": True,
            "sensitivity_simulation_count": 3,
            "sensitivity_covs": [1, 2],
        })
        settings.update(updates)
        return settings

    def run_simulation(self, settings=None, systems=None):
        table = load_votes("../data/2-by-2-example.csv")
        systems = systems or [self.make_system(table)]
        simulation = Simulation(settings or self.settings(), systems, table)
        simulation.simulate()
        result = Sim_result(simulation.attributes())
        result.analysis()
        return result

    def test_single_list_draw_changes_only_one_positive_cell(self):
        votes = np.array([[100., 0., 200.], [50., 0., 0.]])
        for distribution in ("uniform", "gamma", "beta", "log-normal"):
            first = list(single_list_perturbations(votes, 20, .01, distribution, make_rng(72)))
            second = list(single_list_perturbations(votes, 20, .01, distribution, make_rng(72)))
            for (c, p, draw), (c2, p2, draw2) in zip(first, second):
                self.assertEqual((c, p), (c2, p2))
                np.testing.assert_array_equal(draw, draw2)
                self.assertGreater(votes[c, p], 0)
                changed = draw != votes
                self.assertTrue(changed[c, p])
                self.assertEqual(changed.sum(), 1)
                self.assertNotEqual(draw.sum(), votes.sum())

    def test_single_list_categories_are_exclusive(self):
        def election(seats):
            return SimpleNamespace(party_vote_info={"specified": False}, results={
                "all_const_seats": seats, "all_grand_total": np.sum(seats, axis=0)})
        base = election([[2, 2, 2], [2, 2, 2], [2, 2, 2]])
        cases = [
            [[2,2,2], [2,2,2], [2,2,2]],  # unchanged
            [[2,3,1], [2,1,3], [2,2,2]],  # other parties
            [[2,2,2], [3,1,2], [1,3,2]],  # selected party elsewhere
            [[3,1,2], [1,3,2], [2,2,2]],  # selected list
            [[3,1,2], [2,2,2], [2,2,2]],  # party totals take precedence
        ]
        for expected, seats in enumerate(cases):
            self.assertEqual(single_list_category(base, election(seats), 0, 0), expected)

    def test_single_list_settings_and_independent_execution(self):
        for invalid in (0, -1, 1.5, True):
            with self.assertRaisesRegex(ValueError, "single-list"):
                check_simul_settings(self.settings(single_list_sensitivity=True,
                                                    single_list_simulation_count=invalid))
        for ordinary in (False, True):
            result = self.run_simulation(self.settings(
                sensitivity=ordinary, single_list_sensitivity=True,
                single_list_simulation_count=7))
            proportions = [np.array(result.sensitivity_data[m]["avg"])
                           for m in SINGLE_LIST_MEASURES]
            np.testing.assert_allclose(sum(proportions), 1)
            for measure in SINGLE_LIST_MEASURES:
                self.assertEqual(result.stat[measure].n, 2)
                self.assertEqual(result.stat[measure + "_perturbations"].n, 14)
            self.assertEqual("sensitivity_within_parties" in result.stat, ordinary)
            web = result.get_result_web(False)["vuedata"]
            self.assertEqual(web["block_headers"]["singleListNoChange"], "Single-list sensitivity")
            self.assertTrue(web["singleListSelected"][0]["avg"][0]["percentage"])

    def test_single_list_parallel_merging(self):
        table = load_votes("../data/2-by-2-example.csv")
        def run(count, start):
            simulation = Simulation(self.settings(
                simulation_count=count, sensitivity=False, single_list_sensitivity=True,
                single_list_simulation_count=5), [self.make_system(table)], table,
                start_iteration=start)
            simulation.simulate()
            return Sim_result(simulation.attributes())
        whole = run(4, 0)
        merged = run(2, 0)
        merged.combine(run(2, 2))
        whole.analysis()
        merged.analysis()
        for measure in SINGLE_LIST_MEASURES:
            for statistic in ("avg", "se", "std"):
                np.testing.assert_allclose(whole.sensitivity_data[measure][statistic],
                                           merged.sensitivity_data[measure][statistic])

    def test_single_list_saved_statistics_and_reports(self):
        from simulation_chunks import run_chunk, combine_chunks, write_chunk_result, read_chunk_result
        from sim import write_csv
        from input_files import validate_settings
        table = load_votes("../data/2-by-2-example.csv")
        settings = validate_settings(self.settings(
            sensitivity=False, single_list_sensitivity=True, single_list_simulation_count=5))
        self.assertTrue(settings["single_list_sensitivity"])
        self.assertEqual(settings["single_list_simulation_count"], 5)
        stats = run_chunk(table, [self.make_system(table)], settings, 2, 0)
        with TemporaryDirectory() as directory:
            path = Path(directory)
            write_chunk_result(path / "stats.json", stats)
            result = combine_chunks([read_chunk_result(path / "stats.json")])
            write_csv(path / "results.csv", result)
            csv = (path / "results.csv").read_text()
            self.assertIn("Single-list sensitivity", csv)
            self.assertIn("Changes to selected list", csv)
            self.assertIn("Single-list perturbations per major simulation,5", csv)
            SimulationWorkbook(result.get_result_web(False), path / "results.xlsx").write()
            sheet = load_workbook(path / "results.xlsx")["Quality measures"]
            titles = [row[0].value for row in sheet]
            self.assertIn("Single-list sensitivity: Changes to selected list", titles)

    def test_cov_list_sorts_any_order_and_rejects_duplicates(self):
        self.assertEqual(
            sensitivity_covs([2, 0.1, 1, 0.5, 0.2]),
            [0.001, 0.002, 0.005, 0.01, 0.02],
        )
        with self.assertRaisesRegex(ValueError, "at least one"):
            sensitivity_covs([])
        with self.assertRaisesRegex(ValueError, "positive"):
            sensitivity_covs([0, 1])
        with self.assertRaisesRegex(ValueError, "distinct"):
            sensitivity_covs([1, 0.5, 1])

    def test_sensitivity_limit_uses_largest_cov_at_any_position(self):
        settings = self.settings(sensitivity_covs=[58, 1])
        with self.assertRaisesRegex(ValueError, "57.735%"):
            check_simul_settings(settings)

    def test_sensitivity_settings_are_validated(self):
        self.assertEqual(
            SimulationSettings()["sensitivity_simulation_count"], 3)
        self.assertEqual(SimulationSettings()["gen_method"], "log-normal")
        self.assertEqual(SimulationSettings()["sensitivity_gen_method"], "uniform")
        older_settings = SimulationSettings()
        del older_settings["sensitivity_gen_method"]
        self.assertEqual(
            check_simul_settings(older_settings)["sensitivity_gen_method"],
            "uniform")
        settings = self.settings()
        self.assertTrue(check_simul_settings(settings)["sensitivity"])
        descending = self.settings(sensitivity_covs=[2, 1])
        self.assertEqual(
            check_simul_settings(descending)["sensitivity_covs"], [1, 2])
        settings["sensitivity_simulation_count"] = 0
        with self.assertRaisesRegex(ValueError, "positive integer"):
            check_simul_settings(settings)
        settings["sensitivity"] = False
        self.assertFalse(check_simul_settings(settings)["sensitivity"])

    def test_perturbations_preserve_totals_and_zero_cells(self):
        from randomness import make_rng

        votes = [[100, 0, 50], [0, 40, 60]]
        party_votes = [100, 80, 20]
        perturbed, national = generate_perturbations(
            votes, party_votes, 5, 0.1, "log-normal", make_rng(7, (1,)))

        np.testing.assert_allclose(
            perturbed.sum(axis=2),
            np.tile(np.asarray(votes).sum(axis=1), (5, 1)))
        np.testing.assert_allclose(
            national.sum(axis=1), sum(party_votes))
        self.assertTrue(np.all(perturbed[:, 0, 1] == 0))
        self.assertTrue(np.all(perturbed[:, 1, 0] == 0))

    def test_displacement_is_split_between_and_within_parties(self):
        def election(constituencies, totals):
            return SimpleNamespace(
                party_vote_info={"specified": False},
                results={
                    "all_const_seats": constituencies,
                    "all_grand_total": totals,
                },
            )

        base = election([[2, 0], [0, 2]], [2, 2])
        between = election([[1, 1], [0, 2]], [1, 3])
        within = election([[1, 0], [1, 2]], [2, 2])

        np.testing.assert_array_equal(
            seat_displacements([base], [between]), ([1], [0]))
        np.testing.assert_array_equal(
            seat_displacements([base], [within]), ([0], [1]))

    def test_sensitivity_keeps_ordinary_measures_and_averages_by_major(self):
        result = self.run_simulation(self.settings(sensitivity_covs=[2, 1]))

        self.assertEqual(result.stat["const_deviation"].n, 2)
        self.assertEqual(result.stat["sensitivity_between_parties"].n, 2)
        self.assertEqual(
            result.stat["sensitivity_between_parties"].numpy_mean().shape,
            (2, 1),
        )
        self.assertEqual(result.sensitivity_data["covs"], [1, 2])
        self.assertEqual(
            result.stat["sensitivity_between_parties_perturbations"].n, 6)

    def test_single_outer_election_uses_all_inner_displacements(self):
        # The yellow report's failure: one outer mean must not imply zero SD.
        table = load_votes("../data/2-by-2-example.csv")
        systems = [self.make_system(table, name) for name in ("One", "Two")]
        settings = self.settings(
            simulation_count=1, sensitivity_simulation_count=4,
            sensitivity_covs=[0.1])
        with patch("simulate.seat_displacements", side_effect=[
                (np.array([0, 0]), np.array(row))
                for row in ([0, 2], [2, 0], [0, 2], [2, 0])]):
            result = self.run_simulation(settings, systems)
        data = result.sensitivity_data["sensitivity_within_parties"]
        np.testing.assert_allclose(data["avg"], [[1, 1]])
        np.testing.assert_allclose(data["std"], [[np.sqrt(4/3), np.sqrt(4/3)]])
        np.testing.assert_allclose(data["se"], [[np.sqrt(1/3), np.sqrt(1/3)]])
        self.assertEqual(data["min"], [[0, 0]])
        self.assertEqual(data["max"], [[2, 2]])
        self.assertAlmostEqual(data["lo95"][0][0], 1 - 1.96*np.sqrt(1/3))
        web = result.get_result_web(False)["vuedata"]["sensitivityWithin"][0]
        self.assertAlmostEqual(web["avg"][0]["ci"], 1.96*np.sqrt(1/3))

    def test_nested_variance_and_ci_keep_outer_elections_independent(self):
        outer = Running_stats((1, 1))
        individual = Running_stats((1, 1))
        for group in ([0, 2], [4, 6]):
            outer.update([[np.mean(group)]])
            for value in group:
                individual.update([[value]])
        data = sensitivity_statistics(outer, individual)
        # Between means variance is 8; within variance is 2.
        # A+B = 8 + (1-1/2)*2 = 9; Var(grand mean) = 8/2 = 4.
        self.assertEqual(data["avg"], [[3]])
        self.assertEqual(data["std"], [[3]])
        self.assertEqual(data["se"], [[2]])
        self.assertEqual(data["lo95"], [[3 - 1.96*2]])
        self.assertEqual(data["hi95"], [[3 + 1.96*2]])

    def test_one_inner_per_outer_uses_ordinary_sample_uncertainty(self):
        stats = Running_stats((1, 1))
        for value in (0, 2):
            stats.update([[value]])
        data = sensitivity_statistics(stats, stats)
        np.testing.assert_allclose(data["std"], [[np.sqrt(2)]])
        self.assertEqual(data["se"], [[1]])

    def test_one_observation_has_no_estimate_of_uncertainty(self):
        result = self.run_simulation(self.settings(
            simulation_count=1, sensitivity_simulation_count=1))
        data = result.sensitivity_data["sensitivity_within_parties"]
        self.assertEqual(data["std"], [[None], [None]])
        self.assertEqual(data["lo95"], [[None], [None]])
        web = result.get_result_web(False)["vuedata"]["sensitivityWithin"][0]
        self.assertIsNone(web["avg"][0]["ci"])
        self.assertEqual(web["std"], ["–"])

    def test_old_saved_sensitivity_cannot_supply_missing_inner_statistics(self):
        table = load_votes("../data/2-by-2-example.csv")
        simulation = Simulation(self.settings(), [self.make_system(table)], table)
        simulation.simulate()
        saved = simulation.attributes()
        del saved["stat"]["sensitivity_within_parties_perturbations"]
        with self.assertRaisesRegex(ValueError, "Rerun the simulation"):
            Sim_result(saved)

    def test_parallel_sensitivity_results_can_be_read_by_web(self):
        from web import app

        result = self.run_simulation(self.settings(cpu_count=2))
        # parsim.py sends analyzed results without the raw accumulators.
        summary = dict(vars(result))
        del summary["stat"]
        simid = "sensitivity-result"
        process = Mock()
        with TemporaryDirectory() as directory, \
                patch.dict(os.environ, {"VOTING_STATE_DIR": directory}), \
                patch.dict(noweb.SIMULATIONS, {
                    simid: {"kind": "parallel", "process": process}}, clear=True):
            write_sim_dict(simid, summary)
            write_sim_status(simid, {
                "done": True, "iteration": result.iteration,
                "total_time": 0, "time_left": 0})
            response = app.test_client().post("/api/simulate/check/", json={
                "simid": simid, "stop": False})
            payload = response.get_json()

        self.assertNotIn("error", payload)
        self.assertTrue(payload["status"]["done"])
        self.assertEqual(payload["results"]["sensitivity_data"],
                         result.sensitivity_data)
        self.assertEqual(payload["results"]["vuedata"]["sensitivityWithin"],
                         result.get_result_web(True)["vuedata"]["sensitivityWithin"])
        process.wait.assert_called_once()

    def test_sensitivity_combines_reproducibly_across_workers(self):
        table = load_votes("../data/2-by-2-example.csv")
        systems = [self.make_system(table)]

        def run(count, start):
            settings = self.settings(simulation_count=count)
            simulation = Simulation(
                settings, deepcopy(systems), deepcopy(table),
                start_iteration=start)
            simulation.simulate()
            return Sim_result(simulation.attributes())

        uninterrupted = run(4, 0)
        combined = run(2, 0)
        combined.combine(run(2, 2))
        for measure in [*SENS_MEASURES,
                        *[m + "_perturbations" for m in SENS_MEASURES]]:
            np.testing.assert_allclose(
                uninterrupted.stat[measure].numpy_mean(),
                combined.stat[measure].numpy_mean())
            np.testing.assert_allclose(
                uninterrupted.stat[measure].numpy_std(),
                combined.stat[measure].numpy_std())
        uninterrupted.analysis()
        combined.analysis()
        for measure in SENS_MEASURES:
            for statistic in ("avg", "std", "se", "lo95", "hi95", "min", "max"):
                np.testing.assert_allclose(
                    uninterrupted.sensitivity_data[measure][statistic],
                    combined.sensitivity_data[measure][statistic])

    def test_change_fractions_and_clustered_confidence_intervals(self):
        # Outer 1: unchanged, list-only, party-only.
        # Outer 2: all party changes, including simultaneous list movements.
        displacements = [(0, 0), (0, 2), (1, 0), (2, 0), (1, 3), (1, 1)]
        with patch("simulate.seat_displacements", side_effect=[
                (np.array([party]), np.array([within]))
                for party, within in displacements]):
            result = self.run_simulation(self.settings(sensitivity_covs=[1]))
        expected = {
            "sensitivity_list_only_change": (1/6, 1/6),
            "sensitivity_party_change": (2/3, 1/3),
        }
        for measure, (mean, se) in expected.items():
            data = result.sensitivity_data[measure]
            self.assertAlmostEqual(data["avg"][0][0], mean)
            self.assertAlmostEqual(data["se"][0][0], se)
            self.assertEqual(result.stat[measure].n, 2)
            self.assertEqual(result.stat[measure + "_perturbations"].n, 6)
        self.assertAlmostEqual(1 - sum(value[0] for value in expected.values()), 1/6)
        web = result.get_result_web(False)
        vue = web["vuedata"]
        for group, measure in (("sensitivityListOnlyChange", "sensitivity_list_only_change"),
                               ("sensitivityPartyChange", "sensitivity_party_change")):
            entry = vue[group][0]["avg"][0]
            self.assertTrue(entry["percentage"])
            self.assertAlmostEqual(entry["value"], expected[measure][0])
            self.assertAlmostEqual(entry["ci"], 1.96 * expected[measure][1])
        self.assertEqual(vue["block_continues"]["sensitivityBetween"],
                         "sensitivityListOnlyChange")
        self.assertEqual(vue["block_continues"]["sensitivityListOnlyChange"],
                         "sensitivityPartyChange")
        with TemporaryDirectory() as directory:
            path = Path(directory) / "changes.xlsx"
            SimulationWorkbook(web, path).write()
            sheet = load_workbook(path)["Quality measures"]
            title = next(cell for row in sheet for cell in row
                         if cell.value == "Party totals change")
            value = sheet.cell(title.row + 1, 3)
            self.assertAlmostEqual(value.value, 2/3)
            self.assertIn("%", value.number_format)

    def test_entropy_reference_is_not_computed_for_minor_perturbations(self):
        settings = self.settings(entropy_score=True, simulation_count=2)
        with patch.object(
                entropy_score,
                "_optimal_allocation",
                wraps=entropy_score._optimal_allocation) as optimize:
            self.run_simulation(settings)
        self.assertEqual(optimize.call_count, 2)

    def test_sensitivity_is_last_quality_block_on_web_and_in_excel(self):
        result = self.run_simulation()
        web = result.get_result_web(False)
        self.assertEqual(web["vuedata"]["group_ids"][-4:], [
            "sensitivityWithin", "sensitivityBetween",
            "sensitivityListOnlyChange", "sensitivityPartyChange"])
        for group in (
                "cmpListTitle", "cmpList", "cmpPartyTitle", "cmpParty",
                "sensitivityWithin", "sensitivityBetween"):
            self.assertEqual(web["vuedata"]["group_stats"][group], ["avg"])
        for group in ("shareTitle", "toLists", "toPartiesTotal", "other"):
            self.assertNotIn(group, web["vuedata"]["group_stats"])
        self.assertEqual(
            [row["rowtitle"]
             for row in web["vuedata"]["sensitivityWithin"]],
            ["1% CoV", "2% CoV"],
        )

        with TemporaryDirectory() as directory:
            path = Path(directory) / "sensitivity.xlsx"
            SimulationWorkbook(web, path).write()
            sheet = load_workbook(path, read_only=True)["Quality measures"]
            first_column = [
                row[0].value for row in sheet.iter_rows(min_col=1, max_col=1)]
        self.assertLess(
            first_column.index("Seats displaced between lists within parties"),
            first_column.index("Seats displaced between parties"),
        )
        self.assertEqual(first_column.count("1% CoV"), 4)
        self.assertEqual(first_column.count("2% CoV"), 4)


if __name__ == "__main__":
    unittest.main()
