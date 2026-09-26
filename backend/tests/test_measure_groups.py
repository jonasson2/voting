import json
import unittest

from measure_groups import MeasureGroups
from sim_measures import add_vuedata


class MeasureGroupsTest(unittest.TestCase):
    def test_constituency_disparity_follows_geographical_displacement(self):
        systems = [{"name": "System-1", "compare_with": False}]
        groups = MeasureGroups(systems, party_votes_specified=False)
        rows = list(groups["other"]["rows"])
        index = rows.index("geographical_displacement")
        self.assertEqual(rows[index + 1], "constituency_disparity")

        measures = {
            measure: {"avg": 1, "min": 1, "max": 1, "std": 0}
            for measure in groups.get_all_measures(False)
        }
        result = {
            "data": [{"measures": measures}],
            "iteration": 10,
            "systems": systems,
            "vote_table": {"party_vote_info": {"specified": False}},
        }
        add_vuedata(result, parallel=False)
        row = result["vuedata"]["other"][index + 1]
        self.assertEqual(row["avg"][0]["value"], 1)
        self.assertIn("pruned votes", row["tooltip"])

    def test_specific_measures_are_grouped_in_display_order(self):
        systems = [{"name": "System-1", "compare_with": False}]
        groups = MeasureGroups(
            systems, party_votes_specified=False, include_entropy_score=True)
        self.assertEqual(list(groups["other"]["rows"]), [
            "entropy_score",
            "geographical_displacement", "constituency_disparity",
            "max_overrepresentation", "max_underrepresentation",
            "bias_slope", "bias_corr", "excess",
            "max_neg_margin", "freq_neg_margin", "total_overhang",
        ])
        self.assertEqual(groups["other"]["subgroup_starts"], (
            "geographical_displacement", "max_overrepresentation",
            "bias_slope", "max_neg_margin",
        ))
        json.dumps(groups)

    def test_confidence_interval_is_retained_for_zero_mean(self):
        systems = [{"name": "System-1", "compare_with": False}]
        groups = MeasureGroups(systems, party_votes_specified=False)
        measures = {
            measure: {"avg": 0, "min": 0, "max": 0, "std": 0}
            for measure in groups.get_all_measures(False)
        }
        measures["sum_abs"]["std"] = 1
        result = {
            "data": [{"measures": measures}],
            "iteration": 100,
            "systems": systems,
            "vote_table": {"party_vote_info": {"specified": False}},
        }

        add_vuedata(result, parallel=False)

        displayed = result["vuedata"]["toLists"][0]["avg"][0]
        self.assertEqual(displayed["value"], 0)
        self.assertAlmostEqual(displayed["ci"], 0.196)

    def test_comparison_heading_is_omitted_without_comparison_systems(self):
        systems = [{"name": "System-1", "compare_with": False}]

        groups = MeasureGroups(systems, party_votes_specified=False)

        self.assertNotIn("cmpListTitle", groups)
        self.assertNotIn("cmpList", groups)
        self.assertNotIn("cmpPartyTitle", groups)
        self.assertNotIn("cmpParty", groups)

    def test_comparison_heading_is_retained_with_comparison_system(self):
        systems = [{"name": "System-1", "compare_with": True}]

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
        systems = [{"name": "System-1", "compare_with": True}]
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
            {"name": "System-1", "compare_with": True},
            {"name": "System-2", "compare_with": True},
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
        systems = [{"name": "System-1", "compare_with": True}]

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
            {"name": "System-1", "compare_with": True},
            {"name": "System-2", "compare_with": False},
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
                    self.assertTrue(shown["cmpPartyTitle"])
                    self.assertEqual(shown["cmpParty"], has_difference)
                    self.assertEqual(
                        result["vuedata"]["group_messages"].get(
                            "cmpPartyTitle"),
                        None if has_difference else
                        "All tested systems gave identical party seat totals "
                        "in this simulation.")
                    self.assertTrue(shown["cmpListTitle"])
                    self.assertTrue(shown["cmpList"])
                    self.assertTrue(shown["toPartiesTotal"])
                    self.assertEqual(
                        result["data"][1]["measures"][measure]["max"],
                        2 if has_difference else 0)

    def test_entropy_score_is_included_only_when_requested(self):
        systems = [{"name": "System-1", "compare_with": False}]

        without_score = MeasureGroups(systems, False)
        with_score = MeasureGroups(
            systems, False, include_entropy_score=True)

        self.assertNotIn("entropy_score", without_score["other"]["rows"])
        self.assertIn("entropy_score", with_score["other"]["rows"])

    def test_unavailable_entropy_score_is_displayed_as_dash(self):
        systems = [{"name": "System-1", "compare_with": False}]
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

        self.assertEqual(result["vuedata"]["other"][0]["avg"], ["–"])
        self.assertEqual(result["vuedata"]["stats"], ["avg", "std"])
        self.assertEqual(
            result["vuedata"]["stat_headings"],
            {"avg": "Average & 95% confidence interval", "std": "STD.DEV."},
        )
