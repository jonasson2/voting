"""Fill constituency seat totals before enforcing national party totals."""

import numpy as np

from apportion import apportion1d_general
from common_allocate import allocation_step
from ties import remap


def allocate_provisionally(votes, row_totals, prior, divisor_gen, on_tie=None):
    """Fill each constituency independently, without national party limits."""
    prior = np.asarray(prior, dtype=int)
    row_totals = np.asarray(row_totals, dtype=int)
    votes = np.asarray(votes, dtype=float)
    allocation = prior.copy()
    nparty = allocation.shape[1]
    for c, total in enumerate(row_totals):
        allocation[c], _, _ = apportion1d_general(
            v_votes=votes[c],
            num_total_seats=int(total),
            prior_allocations=prior[c],
            rule=divisor_gen,
            on_tie=(remap(on_tie, c * nparty + np.arange(nparty))
                    if on_tie is not None else None),
        )
    return allocation


def divisor_values(divisor_gen, count):
    """Return validated divisor values through the requested seat count."""
    generator = divisor_gen()
    divisors = np.array([next(generator) for _ in range(count + 1)])
    if (not np.isfinite(divisors).all() or (divisors <= 0).any()
            or (np.diff(divisors) < 0).any()):
        raise ValueError(
            "Switching requires positive, finite, nondecreasing divisors.")
    return divisors


def allocate_bounded_provisionally(
        votes, minimum_rows, row_limits, prior,
        divisor_gen, remaining, *, rng=None, on_tie=None):
    """Allocate row minima, then provisionally fill a shared seat pool."""
    votes = np.asarray(votes, dtype=float)
    row_limits = np.asarray(row_limits, dtype=int)
    allocation = allocate_provisionally(
        votes, minimum_rows, prior, divisor_gen, on_tie)
    count = int(row_limits.max()) + 1
    divisors = divisor_values(divisor_gen, count)
    for _ in range(remaining):
        scores = votes / divisors[allocation]
        scores[allocation.sum(axis=1) >= row_limits, :] = -np.inf
        step = allocation_step(
            scores, votes, allocation, divisors, rng, on_tie)
        allocation[step["constituency"], step["party"]] += 1
    return allocation, divisors
