import unittest

from measure_groups import MeasureGroups
from sim_measures import add_vuedata


class MeasureGroupsTest(unittest.TestCase):
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
