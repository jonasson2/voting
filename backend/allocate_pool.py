"""Allocate a shared seat pool within constituency capacities."""

import numpy as np

from common_allocate import allocation_step


def allocate_pool(votes, row_limits, party_targets, prior_alloc, div_gen,
                  seats, compute_scores, reason, *, rng=None, on_tie=None,
                  exclude_zero_votes=False):
    """Allocate a seat pool; row limits are capacities, not desired totals.

    Votes and party targets have already been prepared by the coordinator.
    compute_scores returns a score for every constituency-party pair.
    """
    allocation = np.asarray(prior_alloc, dtype=int).copy()
    free_party = party_targets - allocation.sum(axis=0)
    free_const = row_limits - allocation.sum(axis=1)
    if (free_party < 0).any() or (free_const < 0).any():
        raise ValueError("Allocation targets are below the seats already allocated.")
    if free_party.sum() < seats or free_const.sum() < seats:
        raise ValueError("Insufficient capacity for the remaining adjustment seats.")
    generator = div_gen()
    divisors = np.array([next(generator) for _ in range(int(allocation.max()) + seats + 1)])
    votesums = votes.sum(axis=1)
    steps = []
    for _ in range(seats):
        scores = compute_scores(votes, allocation, divisors, votesums=votesums)
        scores[free_const <= 0, :] = -np.inf
        scores[:, free_party <= 0] = -np.inf
        if exclude_zero_votes:
            scores[votes <= 0] = -np.inf
        step = allocation_step(scores, votes, allocation, divisors, rng, on_tie)
        c, p = step["constituency"], step["party"]
        allocation[c, p] += 1
        free_const[c] -= 1
        free_party[p] -= 1
        step.update(reason=reason, last_party=None, phase="flexible")
        steps.append(step)
    return allocation, steps


def next_quotient(votes, allocation, divisors, **_):
    scores = quotient_scores(votes, allocation, divisors)
    maximum = scores.max()
    return np.nonzero(scores == maximum)[0], maximum


def quotient_scores(votes, allocation, divisors, **_):
    return votes / divisors[allocation]
