import unittest

import numpy as np

from common_allocate import allocate_fixed
from dictionaries import DIVIDER_RULES, FLEXIBLE_ADJUSTMENT_METHODS
from methods.common_methods import rel_sup_simple, superiority_simple
from methods.max_const_votes import max_const_votes


class RelativeSuperiorityFlexTest(unittest.TestCase):
    def test_flexible_pool_differs_from_maximum_votes(self):
        votes = np.array([[33, 40, 2], [40, 23, 26], [31, 15, 48]])
        targets = [2, 2, 1]
        prior = np.zeros_like(votes)
        bounds = dict(num_adjustment_seats=5, min_adj_seats=[0, 0, 0],
                      max_adj_seats=[3, 3, 3])

        allocation, demo = rel_sup_simple(
            votes, [0, 0, 0], targets, prior,
            DIVIDER_RULES['sainte-lague'], **bounds)
        max_votes, _ = max_const_votes(
            votes, [0, 0, 0], targets, prior,
            DIVIDER_RULES['sainte-lague'], **bounds)

        np.testing.assert_array_equal(
            allocation, [[1, 1, 0], [0, 1, 0], [1, 0, 1]])
        np.testing.assert_array_equal(
            max_votes, [[1, 1, 0], [1, 1, 0], [0, 0, 1]])
        self.assertEqual(
            [(step['constituency'], step['party'])
             for step in demo['data']['sequence']],
            [(0, 1), (2, 2), (0, 0), (2, 0), (1, 1)])
        self.assertAlmostEqual(demo['data']['sequence'][0]['maximum'], 3.0)
        self.assertIn('relative-sup-simple', FLEXIBLE_ADJUSTMENT_METHODS)

    def test_exact_bounds_keep_fixed_allocation(self):
        votes = np.array([[33, 40, 2], [40, 23, 26], [31, 15, 48]])
        prior = np.zeros_like(votes)
        divider = DIVIDER_RULES['sainte-lague']
        expected, _ = allocate_fixed(
            votes, [2, 1, 2], [2, 2, 1], prior, divider,
            superiority_simple, 'Superiority ratio', 'test')

        actual, demo = rel_sup_simple(
            votes, [2, 1, 2], [2, 2, 1], prior, divider,
            num_adjustment_seats=5, min_adj_seats=[2, 1, 2],
            max_adj_seats=[2, 1, 2])

        np.testing.assert_array_equal(actual, expected)
        self.assertTrue(all(step['phase'] == 'minimum'
                            for step in demo['data']['sequence']))

    def test_minimums_maxima_and_national_seats(self):
        votes = [[33, 40, 2], [40, 23, 26], [31, 15, 48]]
        allocation, demo = rel_sup_simple(
            votes, [1, 0, 0], [3, 2, 1], np.zeros((3, 3), dtype=int),
            DIVIDER_RULES['sainte-lague'], num_adjustment_seats=5,
            min_adj_seats=[1, 0, 0], max_adj_seats=[2, 2, 2],
            nat_prior_allocations=[1, 0, 0])

        np.testing.assert_array_equal(allocation.sum(axis=1), [2, 1, 2])
        np.testing.assert_array_equal(allocation.sum(axis=0), [2, 2, 1])
        self.assertEqual([step['phase'] for step in demo['data']['sequence']],
                         ['minimum'] + ['flexible'] * 4)

if __name__ == '__main__':
    unittest.main()
