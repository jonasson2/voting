import unittest

import numpy as np

from dictionaries import ADJUSTMENT_METHODS
from division_rules import dhondt_gen
from methods.switching import switching
from methods.switching_flex import improve_by_exchanges
from math import log
from table_util import entropy


class EntropyExchangeTest(unittest.TestCase):
    def test_exchange_improves_normal_switching_and_preserves_both_margins(self):
        votes = np.array([[1000, 500, 200], [500, 600, 800], [1000, 900, 400]])
        prior = np.zeros((3, 3), dtype=int)
        normal, _ = switching(votes, [2] * 3, [2] * 3, prior, dhondt_gen)
        improved, exchanges = improve_by_exchanges(votes, normal, prior, dhondt_gen)

        np.testing.assert_array_equal(improved, [[1, 1, 0], [0, 0, 2], [1, 1, 0]])
        np.testing.assert_array_equal(improved.sum(axis=0), normal.sum(axis=0))
        np.testing.assert_array_equal(improved.sum(axis=1), normal.sum(axis=1))
        self.assertEqual(len(exchanges), 1)
        self.assertAlmostEqual(exchanges[0]['log_gain'], log(5 / 3))
        self.assertAlmostEqual(
            entropy(votes, improved, dhondt_gen) - entropy(votes, normal, dhondt_gen),
            sum(step['log_gain'] for step in exchanges))
        self.assertNotIn('switching-plus', ADJUSTMENT_METHODS)

    def test_exchanges_protect_fixed_seats(self):
        allocation = np.array([[1, 0], [0, 1]])
        protected = np.array([[1, 0], [0, 0]])
        improved, exchanges = improve_by_exchanges(
            [[50, 100], [100, 50]], allocation, protected, dhondt_gen)

        np.testing.assert_array_equal(improved, allocation)
        self.assertEqual(exchanges, [])

    def test_equal_product_is_not_exchanged(self):
        allocation = np.array([[1, 0], [0, 1]])
        improved, exchanges = improve_by_exchanges(
            [[100, 100], [100, 100]], allocation,
            np.zeros((2, 2), dtype=int), dhondt_gen)

        np.testing.assert_array_equal(improved, allocation)
        self.assertEqual(exchanges, [])

