import unittest

from sim_measures import normalize_negative_zero


class SimulationMeasuresTest(unittest.TestCase):
    def test_tiny_negative_value_becomes_zero(self):
        self.assertEqual(normalize_negative_zero(-1e-12), 0)

    def test_meaningful_negative_value_is_unchanged(self):
        self.assertEqual(normalize_negative_zero(-0.001), -0.001)

    def test_positive_value_is_unchanged(self):
        self.assertEqual(normalize_negative_zero(1e-12), 1e-12)
