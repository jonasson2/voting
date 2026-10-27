"""RSSS absolute MinL1 and MinL2, with prescribed constituency totals.

Minimize sum(abs(s-q)) or sum((s-q)**2), without relative-error or
constituency weights. The adjustment divisor does not enter either objective.
"""

from functools import partial

import numpy as np

from common_allocate import common_allocate, print_demo_table
from division_rules import dhondt_gen
from methods.seat_share import local_reference, print_exact, print_improvements
from methods.seat_lp import allocate_by_marginal_costs
from methods.seat_switching import improve_by_costs
from reference_scaling import _scale_to_both_margins


def reference_seats(votes, row_totals, party_totals, prior, scaling, options):
    reference, rows, prior = local_reference(votes, row_totals, prior, options)
    if scaling == "both":
        targets = np.asarray(party_totals, dtype=float)
        national_fixed = options.get("nat_prior_allocations")
        if national_fixed is not None:
            targets = targets - np.asarray(national_fixed)
        try:
            _scale_to_both_margins(reference, rows, targets, int(rows.sum()))
        except RuntimeError as error:
            raise ValueError(f"MinL1/MinL2 double scaling: {error}") from error
        if (not np.allclose(reference.sum(axis=1), rows, atol=1e-8, rtol=0)
                or (np.isclose(rows.sum(), targets.sum())
                    and not np.allclose(reference.sum(axis=0), targets, atol=1e-8, rtol=0))):
            raise ValueError("MinL1/MinL2 double scaling cannot satisfy the reference seat totals.")
    return reference, rows, prior


def marginal_costs(reference, seats, power):
    difference = seats - reference
    return (abs(difference + 1) - abs(difference) if power == 1
            else 2 * difference + 1)


def allocate(votes, row_totals, party_totals, prior, divisor_gen=None, *,
             power, scaling, approximate=False, **kwargs):
    reference, rows, prior = reference_seats(
        votes, row_totals, party_totals, prior, scaling, kwargs)

    if approximate:
        return switching(reference, rows, party_totals, prior, power, kwargs)

    def costs(variables):
        return np.array([
            marginal_costs(reference[c, p], k, power)
            for c, p, k in variables
        ])

    allocation = allocate_by_marginal_costs(
        rows, party_totals, prior, costs, eligible=np.asarray(votes) > 0,
        name=f"MinL{power}", **kwargs)
    return allocation, {"data": [], "function": print_exact}


def switching(reference, rows, party_totals, prior, power, options):
    def criterion(q, seats, _divisors, **_):
        scores = -marginal_costs(q, seats, power)
        return np.flatnonzero(scores == scores.max()), scores.max()

    try:
        allocation, initial = common_allocate(
            reference, rows, party_totals, prior, dhondt_gen,
            criterion, "Negative marginal cost", "Smallest marginal cost",
            vote_floor=None, exclude_zero_votes=True,
            **{key: value for key, value in options.items()
               if key not in {"vote_floor", "exclude_zero_votes", "last"}})
    except ValueError:
        allocation = allocate_by_marginal_costs(
            rows, party_totals, prior, lambda variables: np.zeros(len(variables)),
            eligible=reference > 0, name=f"MinL{power} starting allocation", **options)
        initial = None

    def costs(seats):
        return np.where(reference > 0, marginal_costs(reference, seats, power), np.inf)

    allocation, exchanges = improve_by_costs(allocation, prior, costs)
    return allocation, {
        "data": {"initial": initial, "exchanges": exchanges},
        "functions": [print_initial, print_improvements],
    }


def print_initial(system, steps):
    if steps["initial"] is None:
        return [], [], "Initial feasible allocation from network LP"
    headers, rows, _ = print_demo_table(system, steps["initial"]["data"])
    return headers, rows, "Initial allocation by smallest marginal cost"


min_l1_const = partial(allocate, power=1, scaling="const")
min_l1_double = partial(allocate, power=1, scaling="both")
min_l2_const = partial(allocate, power=2, scaling="const")
min_l2_double = partial(allocate, power=2, scaling="both")
min_l1_const_switching = partial(allocate, power=1, scaling="const", approximate=True)
min_l1_double_switching = partial(allocate, power=1, scaling="both", approximate=True)
min_l2_const_switching = partial(allocate, power=2, scaling="const", approximate=True)
min_l2_double_switching = partial(allocate, power=2, scaling="both", approximate=True)
