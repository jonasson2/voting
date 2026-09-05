import unittest

from measure_groups import MeasureGroups


class MeasureGroupsTest(unittest.TestCase):
    def test_comparison_heading_is_omitted_without_comparison_systems(self):
        systems = [{"name": "System-1", "compare_with": False}]

        groups = MeasureGroups(systems, party_votes_specified=False)

        self.assertNotIn("compTitle", groups)
        self.assertNotIn("cmpSys", groups)

    def test_comparison_heading_is_retained_with_comparison_system(self):
        systems = [{"name": "System-1", "compare_with": True}]

        groups = MeasureGroups(systems, party_votes_specified=False)

        self.assertIn("compTitle", groups)
        self.assertIn("cmpSys", groups)
