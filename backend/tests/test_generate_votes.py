import unittest
from unittest.mock import Mock

import numpy as np

from generate_votes import generate_votes
from randomness import make_rng


class GenerateVotesTest(unittest.TestCase):
    distributions = ("uniform", "gamma", "beta")

    def test_draws_are_batched_and_continuous_with_zeros_preserved(self):
        votes = [[0, 100, 200], [300, 0, 0.5]]
        for distribution, method in zip(self.distributions, ("unif", "gamma", "beta")):
            with self.subTest(distribution=distribution):
                rng = Mock(wraps=make_rng(42))
                result = np.array(generate_votes(votes, 0.25, distribution, rng))
                self.assertEqual(result.shape, (2, 3))
                self.assertTrue(np.isfinite(result).all())
                self.assertTrue((result >= 0).all())
                np.testing.assert_array_equal(result[np.array(votes) == 0], 0)
                self.assertTrue((result != np.round(result)).any())
                self.assertGreater(result[1, 2], 0)
                self.assertEqual(len(rng.mock_calls), 1)
                self.assertEqual(getattr(rng, method).call_args.kwargs['size'], (2, 3))

    def test_zero_variation_returns_exact_votes_without_drawing(self):
        votes = [[0, 100.25], [20, 0.5]]
        for distribution in self.distributions:
            with self.subTest(distribution=distribution):
                rng = Mock()
                self.assertEqual(generate_votes(votes, 0, distribution, rng), votes)
                self.assertEqual(rng.mock_calls, [])

    def test_seed_reproducibility(self):
        for distribution in self.distributions:
            with self.subTest(distribution=distribution):
                first = generate_votes([[10, 100]], 0.25, distribution, make_rng(42))
                repeat = generate_votes([[10, 100]], 0.25, distribution, make_rng(42))
                other = generate_votes([[10, 100]], 0.25, distribution, make_rng(43))
                self.assertEqual(first, repeat)
                self.assertNotEqual(first, other)

    def test_distribution_mean_and_relative_sd(self):
        means = np.tile([0.5, 100, 10000], (50000, 1))
        for distribution in self.distributions:
            with self.subTest(distribution=distribution):
                result = np.array(generate_votes(means, 0.25, distribution, make_rng(42)))
                factors = result / means
                np.testing.assert_allclose(factors.mean(axis=0), 1, atol=0.005)
                np.testing.assert_allclose(factors.std(axis=0), 0.25, atol=0.005)
                if distribution == "beta":
                    self.assertTrue(((factors >= 0) & (factors <= 2)).all())

    def test_uniform_wide_interval_is_clipped_at_zero(self):
        result = np.array(generate_votes([[100] * 50000], 1, "uniform", make_rng(42)))
        upper = 100 * (1 + np.sqrt(3))
        self.assertTrue(((result >= 0) & (result <= upper)).all())
        self.assertAlmostEqual(result.mean(), upper / 2, delta=1)

    def test_unknown_distribution_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown vote-generating distribution'):
            generate_votes([[100]], 0.25, 'unknown', make_rng(42))
