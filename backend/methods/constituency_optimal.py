"""Logarithmic optima protecting independent constituency allocations."""

from functools import partial

import numpy as np

from common_allocate import prepare_adjustment_bounds
from methods.optimal_lp import optimal_lp, _divisors
from methods.provisional_allocation import allocate_provisionally


def allocate(votes, row_totals, party_totals, prior, divisor_gen, *,
             one_way=False, **kwargs):
    prior = np.asarray(prior, dtype=int)
    minimums, total, _ = prepare_adjustment_bounds(
        prior.sum(axis=1), row_totals, kwargs)
    if total != int(minimums.sum()):
        raise ValueError("Constituency-protected optima require fixed constituency totals.")
    rows = prior.sum(axis=1) + minimums
    targets = np.asarray(party_totals, dtype=int)
    national_fixed = kwargs.get("nat_prior_allocations")
    if national_fixed is not None:
        targets = targets - np.asarray(national_fixed, dtype=int)
    if int(targets.sum()) != int(rows.sum()):
        raise ValueError(
            "Constituency-protected optima require prescribed constituency party totals; "
            "national adjustment seats are not supported.")
    if (prior.sum(axis=0) > targets).any():
        raise ValueError("Party targets are below protected fixed seats.")

    # Match Biproportional rounding's handling of votes below one.
    votes = np.maximum(np.asarray(votes, dtype=float), 1)
    _divisors(divisor_gen, int(rows.max(initial=0)))
    baseline = allocate_provisionally(
        votes, rows, prior, divisor_gen, kwargs.get("on_tie"))
    difference = baseline.sum(axis=0) - targets
    lower = prior.copy()
    upper = prior + total
    exact = difference == 0
    lower[:, exact] = baseline[:, exact]
    upper[:, exact] = baseline[:, exact]
    if one_way:
        lower[:, difference < 0] = baseline[:, difference < 0]
        upper[:, difference > 0] = baseline[:, difference > 0]
    return optimal_lp(
        votes, rows, party_totals, prior, divisor_gen,
        list_lower_bounds=lower, list_upper_bounds=upper, **kwargs)


exact_parties_intact = partial(allocate, one_way=False)
one_way = partial(allocate, one_way=True)
