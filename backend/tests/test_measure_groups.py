import json
import unittest

from measure_groups import MeasureGroups
from sim_measures import add_vuedata


class MeasureGroupsTest(unittest.TestCase):
    def test_sections_and_optional_rows_follow_design(self):
        groups = MeasureGroups([{"name": "System-1"}], False,
                               include_entropy_score=True,
                               scalings=["const", "both", "party", "total"])
        self.assertEqual(list(groups)[:8], [
            "const", "entropy", "both", "party", "total", "parity",
            "toPartiesTotal", "singleSeat"])
        self.assertEqual(list(groups["const"]["rows"])[:7], [
            "lh_lists", "local_squared", "const_deviation", "const_surplus",
            "const_shortfall", "const_share_surplus", "const_share_shortfall"])
        self.assertEqual(list(groups["parity"]["rows"]),
                         ["constituency_disparity", "lh_constituencies"])
        self.assertEqual(len(groups["both"]["options"]), 4)
        self.assertEqual(groups["singleSeat"]["option"], "show_single_seat")
        self.assertEqual(len(groups["singleSeat"]["rows"]), 6)
        json.dumps(groups)

    def test_confidence_interval_is_retained_for_zero_mean(self):
        systems = [{"name": "System-1"}]
        groups = MeasureGroups(systems, party_votes_specified=False)
        measures = {
            measure: {"avg": 0, "min": 0, "max": 0, "std": 0}
            for measure in groups.get_all_measures(False)
        }
        measures["const_deviation"]["std"] = 1
        result = {
            "data": [{"measures": measures}],
            "iteration": 100,
            "systems": systems,
            "vote_table": {"party_vote_info": {"specified": False}},
        }

        add_vuedata(result, parallel=False)

        displayed = result["vuedata"]["const"][2]["avg"][0]
        self.assertEqual(displayed["value"], 0)
        self.assertAlmostEqual(displayed["ci"], 0.196)

    def test_every_system_is_included_despite_legacy_selection(self):
        systems = [
            {"name": "System-1", "compare_with": False},
            {"name": "System-2"},
        ]

        groups = MeasureGroups(systems, party_votes_specified=False)

        self.assertIn("cmpListTitle", groups)
        self.assertIn("cmpPartyTitle", groups)
        self.assertEqual(list(groups["cmpList"]["rows"]), [
            "cmp_System-1_const", "cmp_System-2_const"])
        self.assertEqual(list(groups["cmpParty"]["rows"]), [
            "cmp_System-1_tot", "cmp_System-2_tot"])

    def test_comparison_heading_is_retained_with_comparison_system(self):
        systems = [{"name": "System-1"}]

        groups = MeasureGroups(systems, party_votes_specified=False)

        self.assertIn("cmpListTitle", groups)
        self.assertIn("cmpList", groups)
        self.assertIn("cmpPartyTitle", groups)
        self.assertIn("cmpParty", groups)
        self.assertEqual(
            list(groups["cmpList"]["rows"]), ["cmp_System-1_const"])
        self.assertEqual(
            list(groups["cmpParty"]["rows"]), ["cmp_System-1_tot"])

    def test_single_system_hides_both_web_comparisons_without_a_message(self):
        systems = [{"name": "System-1"}]
        groups = MeasureGroups(systems, party_votes_specified=False)
        measures = {
            measure: {"avg": 0, "min": 0, "max": 0, "std": 0}
            for measure in groups.get_all_measures(False)
        }
        result = {
            "data": [{"measures": measures}],
            "iteration": 10,
            "systems": systems,
            "vote_table": {"party_vote_info": {"specified": False}},
        }

        add_vuedata(result, parallel=False)

        for group in ("cmpListTitle", "cmpList", "cmpPartyTitle", "cmpParty"):
            self.assertFalse(result["vuedata"]["show"][group])
        self.assertEqual(result["vuedata"]["group_messages"], {})
        self.assertIn("cmp_System-1_tot", result["data"][0]["measures"])

    def test_only_self_comparisons_are_blank(self):
        systems = [
            {"name": "System-1"},
            {"name": "System-2"},
        ]
        groups = MeasureGroups(systems, party_votes_specified=False)
        measures = {
            measure: {"avg": 0, "min": 0, "max": 0, "std": 0}
            for measure in groups.get_all_measures(False)
        }
        result = {
            "data": [{"measures": measures}, {"measures": measures}],
            "iteration": 10,
            "systems": systems,
            "vote_table": {"party_vote_info": {"specified": False}},
        }

        add_vuedata(result, parallel=False)

        for group in ("cmpList", "cmpParty"):
            rows = result["vuedata"][group]
            self.assertEqual(rows[0]["avg"][0], "")
            self.assertEqual(rows[1]["avg"][1], "")
            self.assertEqual(rows[0]["std"][0], "")
            self.assertEqual(rows[1]["std"][1], "")
            self.assertEqual(rows[0]["avg"][1]["value"], 0)
            self.assertEqual(rows[1]["avg"][0]["value"], 0)

    def test_national_vote_comparisons_remain_available_for_excel(self):
        systems = [{"name": "System-1"}]

        groups = MeasureGroups(systems, party_votes_specified=True)

        comparison_measures = {
            measure
            for group in ("cmpList", "cmpParty", "cmpNationalDetails")
            for measure in groups[group]["rows"]
        }
        self.assertEqual(comparison_measures, {
            "cmp_System-1_const",
            "cmp_System-1_tot",
            "cmp_System-1_nat",
            "cmp_System-1_grand",
        })
        self.assertTrue(groups["cmpNationalDetails"]["onlyExcel"])

    def test_party_comparison_is_hidden_only_when_all_differences_are_zero(self):
        systems = [
            {"name": "System-1"},
            {"name": "System-2"},
        ]
        for national_votes in (False, True):
            for has_difference in (False, True):
                with self.subTest(
                        national_votes=national_votes,
                        has_difference=has_difference):
                    groups = MeasureGroups(systems, national_votes)
                    data = [{"measures": {
                        measure: {"avg": 0, "min": 0, "max": 0, "std": 0}
                        for measure in groups.get_all_measures(national_votes)
                    }} for _ in systems]
                    measure = next(iter(groups["cmpParty"]["rows"]))
                    if has_difference:
                        data[1]["measures"][measure].update(
                            avg=0.0002, max=2, std=0.02)
                    result = {
                        "data": data,
                        "iteration": 10000,
                        "systems": systems,
                        "vote_table": {
                            "party_vote_info": {"specified": national_votes}},
                    }

                    add_vuedata(result, parallel=False)

                    shown = result["vuedata"]["show"]
                    self.assertFalse(shown["cmpPartyTitle"])
                    self.assertTrue(shown["cmpParty"])
                    self.assertEqual(
                        result["vuedata"]["group_messages"].get(
                            "cmpParty"),
                        None if has_difference else
                        "All tested systems gave identical party seat totals "
                        "in this simulation.")
                    self.assertFalse(shown["cmpListTitle"])
                    self.assertTrue(shown["cmpList"])
                    display = result["vuedata"]
                    self.assertTrue(display["block_headers"]["cmpList"])
                    self.assertEqual(display["initial_title"],
                                     "List allocation quality measures")
                    self.assertEqual(display["block_headers"]["parity"],
                                     "Total allocation quality measures")
                    self.assertEqual(display["block_continues"]["parity"],
                                     "toPartiesTotal")
                    self.assertEqual(display["block_continues"]["cmpList"], "cmpParty")
                    self.assertTrue(display["side_titles"]["cmpParty"])
                    self.assertEqual(display["group_titles"]["cmpList"],
                                     "Total list seat\ndifference")
                    self.assertTrue(shown["toPartiesTotal"])
                    self.assertEqual(
                        result["data"][1]["measures"][measure]["max"],
                        2 if has_difference else 0)

    def test_entropy_score_is_included_only_when_requested(self):
        systems = [{"name": "System-1"}]

        without_score = MeasureGroups(systems, False)
        with_score = MeasureGroups(
            systems, False, include_entropy_score=True)

        self.assertNotIn("entropy_score", without_score.get("entropy", {}).get("rows", {}))
        self.assertIn("entropy_score", with_score["entropy"]["rows"])
        two_systems = MeasureGroups(
            [{"name": "System-1"}, {"name": "System-2"}], False,
            include_entropy_score=True)
        self.assertIn("entropy_relative", two_systems["entropy"]["rows"])
        self.assertNotIn("entropy_relative", two_systems["secondary"]["rows"])
        self.assertNotIn("entropy_relative", with_score["entropy"]["rows"])

    def test_unavailable_entropy_score_is_displayed_as_dash(self):
        systems = [{"name": "System-1"}]
        groups = MeasureGroups(systems, False, include_entropy_score=True)
        measures = {
            measure: {"avg": 0, "min": 0, "max": 0, "std": 0}
            for measure in groups.get_all_measures(False)
        }
        result = {
            "data": [{"measures": measures}],
            "iteration": 10,
            "systems": systems,
            "sim_settings": {"entropy_score": True},
            "entropy_score_available": [False],
            "vote_table": {"party_vote_info": {"specified": False}},
        }

        add_vuedata(result, parallel=False)

        self.assertEqual(result["vuedata"]["entropy"][0]["avg"], ["–"])
        self.assertEqual(result["vuedata"]["stats"], ["avg", "std"])
        self.assertEqual(
            result["vuedata"]["stat_headings"],
            {"avg": "Average & 95% confidence interval", "std": "STD.DEV."},
        )
