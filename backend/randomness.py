"""Randompack helpers for simulation and the historical optimal method."""

import randompack


def make_rng(seed=None, spawn_key=()):
    rng = randompack.Rng("x256++", bitexact=True)
    if seed is not None:
        rng.seed(seed, spawn_key=list(spawn_key))
    return rng


def random_uniform(rng, lower, upper):
    """Return a uniform draw, accepting legacy NumPy generators."""
    if lower == upper:
        return float(lower)
    if hasattr(rng, "uniform"):
        return float(rng.uniform(lower, upper))
    return float(rng.unif(a=lower, b=upper))
