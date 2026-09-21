"""Fill constituency seat totals before enforcing national party totals."""

import numpy as np

from apportion import apportion1d_general
from common_allocate import allocation_step
from ties import remap


def allocate_provisionally(votes, row_totals, party_totals, prior,
                           divisor_gen, on_tie=None):
    prior = np.asarray(prior, dtype=int)
    row_totals = np.asarray(row_totals, dtype=int)
    party_totals = np.asarray(party_totals, dtype=int)
    if int(party_totals.sum()) < int(row_totals.sum()):
        raise ValueError("Party-seat totals are below the constituency-seat total.")

    available_votes = np.asarray(votes, dtype=float).copy()
    available_votes[:, prior.sum(axis=0) >= party_totals] = 0
    allocation = prior.copy()
    nparty = allocation.shape[1]
    for c, total in enumerate(row_totals):
        allocation[c], _, _ = apportion1d_general(
            v_votes=available_votes[c],
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
        votes, minimum_rows, row_limits, party_targets, prior,
        divisor_gen, remaining, *, rng=None, on_tie=None):
    """Allocate row minima, then provisionally fill a shared seat pool."""
    votes = np.asarray(votes, dtype=float)
    row_limits = np.asarray(row_limits, dtype=int)
    party_targets = np.asarray(party_targets, dtype=int)
    allocation = allocate_provisionally(
        votes, minimum_rows, party_targets, prior, divisor_gen, on_tie)
    count = max(int(row_limits.max()), int(party_targets.max())) + 1
    divisors = divisor_values(divisor_gen, count)
    available = np.asarray(prior, dtype=int).sum(axis=0) < party_targets
    for _ in range(remaining):
        scores = votes / divisors[allocation]
        scores[allocation.sum(axis=1) >= row_limits, :] = -np.inf
        scores[:, ~available] = -np.inf
        step = allocation_step(
            scores, votes, allocation, divisors, rng, on_tie)
        allocation[step["constituency"], step["party"]] += 1
    return allocation, divisors
