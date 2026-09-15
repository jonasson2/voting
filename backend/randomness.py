"""Randompack helpers shared by vote generation and allocation ties."""

import randompack


def make_rng(seed=None, spawn_key=()):
    rng = randompack.Rng("x256++", bitexact=True)
    if seed is not None:
        rng.seed(seed, spawn_key=list(spawn_key))
    return rng


def random_index(rng, size):
    """Return a uniformly selected index, accepting legacy NumPy generators."""
    if size <= 0:
        raise ValueError("Cannot select from an empty sequence.")
    if hasattr(rng, "integers"):
        return int(rng.integers(size))
    return int(rng.int(0, size - 1))


def random_permutation(rng, size):
    """Return a random permutation, accepting legacy NumPy generators."""
    if hasattr(rng, "permutation"):
        return rng.permutation(size)
    # Randompack's perm returns a permutation of 1..n; NumPy uses 0..n-1.
    return rng.perm(size) - 1


def random_uniform(rng, lower, upper):
    """Return a uniform draw, accepting legacy NumPy generators."""
    if hasattr(rng, "uniform"):
        return float(rng.uniform(lower, upper))
    return float(rng.unif(a=lower, b=upper))
