"""Minimum-first adjustment allocation followed by a bounded national pool."""

import numpy as np

from common_allocate import allocation_step, common_allocate


def common_flex_allocate(votes, row_limits, party_targets, prior_alloc, div_gen,
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


def allocate_with_bounds(votes, row_targets, party_targets, prior_alloc, div_gen,
                         criterion, criterion_name, reason, *, flex_scores, **kwargs):
    """Coordinate exact constituency minima and the remaining national pool."""
    votes = np.asarray(votes, dtype=float)
    vote_floor = kwargs.get("vote_floor", 1)
    if vote_floor is not None:
        votes = np.maximum(votes, vote_floor)
    prior = np.asarray(prior_alloc, dtype=int)
    base = prior.sum(axis=1)
    minimums = np.asarray(kwargs.get("min_adj_seats", np.asarray(row_targets) - base), dtype=int)
    total = int(kwargs.get("num_adjustment_seats", minimums.sum()))
    maxima = kwargs.get("max_adj_seats", minimums)
    if len(minimums) != len(base) or len(maxima) != len(base):
        raise ValueError("Adjustment-seat bounds do not match the constituencies.")
    if (minimums < 0).any():
        raise ValueError("Adjustment-seat minimums must be non-negative.")
    if total < int(minimums.sum()):
        raise ValueError("Constituency minimums exceed the adjustment-seat total.")
    if any(maximum is not None and maximum < minimum
           for minimum, maximum in zip(minimums, maxima)):
        raise ValueError("An adjustment-seat maximum is below its constituency minimum.")
    capacity = np.array([total if maximum is None else maximum for maximum in maxima], dtype=int)
    if int(capacity.sum()) < total:
        raise ValueError("Constituency maxima prevent allocation of all adjustment seats.")

    targets = np.asarray(party_targets, dtype=int)
    national_fixed = kwargs.get("nat_prior_allocations")
    if national_fixed is not None:
        targets = targets - np.asarray(national_fixed, dtype=int)
    deficits = targets - prior.sum(axis=0)
    if (deficits < 0).any():
        raise ValueError("Adjustment seats cannot resolve a party excess.")
    if int(deficits.sum()) < total:
        raise ValueError("Party deficits are smaller than the adjustment-seat total.")

    options = {key: kwargs.get(key) for key in ("rng", "on_tie")}
    options["exclude_zero_votes"] = kwargs.get("exclude_zero_votes", False)
    allocation, demo = common_allocate(
        votes, base + minimums, targets, prior, div_gen,
        criterion, criterion_name, reason, vote_floor=None, **options)
    steps = demo["data"]["sequence"]
    for step in steps:
        step["phase"] = "minimum"
    remaining = total - int(minimums.sum())
    if remaining:
        allocation, extra = common_flex_allocate(
            votes, base + capacity, targets, allocation, div_gen,
            remaining, flex_scores, reason, **options)
        steps.extend(extra)
        if minimums.any():
            for step in steps:
                phase = "Constituency minimum" if step["phase"] == "minimum" else "Remaining pool"
                step["reason"] = f'{phase}: {reason}'

    added = allocation.sum(axis=1) - base
    if (int(added.sum()) != total or (added < minimums).any()
            or (added > capacity).any() or (allocation.sum(axis=0) > targets).any()):
        raise RuntimeError("Adjustment-seat allocation violated its totals or bounds.")
    return allocation, demo


def next_quotient(votes, allocation, divisors, **_):
    scores = quotient_scores(votes, allocation, divisors)
    maximum = scores.max()
    return np.nonzero(scores == maximum)[0], maximum


def quotient_scores(votes, allocation, divisors, **_):
    return votes / divisors[allocation]
