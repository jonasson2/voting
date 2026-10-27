"""Exact and switching allocation using cumulative divisor costs d(k)/q."""

import numpy as np

from allocate_pool import next_quotient
from common_allocate import common_allocate, prepare_adjustment_bounds, print_demo_table
from division_rules import sainte_lague_gen
from methods.seat_lp import allocate_by_marginal_costs
from methods.provisional_allocation import divisor_values
from methods.seat_switching import improve_by_costs, print_exchanges


def local_reference(votes, row_totals, prior, options):
    """Use actual votes and fixed final row totals, with no vote floor."""
    votes = np.asarray(votes, dtype=float)
    prior = np.asarray(prior, dtype=int)
    if (votes.shape != prior.shape or votes.ndim != 2
            or not np.isfinite(votes).all() or (votes < 0).any()):
        raise ValueError("Seat-share allocation requires matching, non-negative finite votes and seats.")
    minimums, total, _ = prepare_adjustment_bounds(
        prior.sum(axis=1), row_totals, options)
    if total != int(minimums.sum()):
        raise ValueError("Seat-share allocation requires fixed constituency seat totals.")
    rows = prior.sum(axis=1) + minimums
    totals = votes.sum(axis=1)[:, None]
    reference = np.divide(votes, totals, out=np.zeros_like(votes), where=totals > 0)
    reference *= rows[:, None]
    if np.any((reference == 0) & (prior > 0)):
        raise ValueError("Seat-share allocation cannot retain a seat on a zero-vote list.")
    return reference, rows, prior


def _allocate(reference, rows, party_totals, prior, divisors, options, *, feasibility=False):
    def costs(variables):
        return np.array([
            0.0 if feasibility else divisors[k] / reference[c, p]
            for c, p, k in variables
        ])

    return allocate_by_marginal_costs(
        rows, party_totals, prior, costs, eligible=reference > 0,
        name="Seat-share allocation", **options)


def exact(votes, row_totals, party_totals, prior, divisor_gen=sainte_lague_gen, **kwargs):
    """Minimize cumulative d(k)/q costs; Sainte-Laguë minimizes sum(s²/q)."""
    reference, rows, prior = local_reference(votes, row_totals, prior, kwargs)
    divisors = divisor_values(divisor_gen, int(rows.max(initial=0)))
    allocation = _allocate(reference, rows, party_totals, prior, divisors, kwargs)
    return allocation, {"data": [], "function": print_exact}


def switching(votes, row_totals, party_totals, prior, divisor_gen=sainte_lague_gen, **kwargs):
    """Fill seats by q/d(k), then improve by reciprocal pair exchanges."""
    reference, rows, prior = local_reference(votes, row_totals, prior, kwargs)
    divisors = divisor_values(divisor_gen, int(rows.max(initial=0)))
    try:
        allocation, initial = common_allocate(
            reference, rows, party_totals, prior, divisor_gen,
            next_quotient, "Local fractional-seat quotient",
            "Maximum local fractional-seat quotient", vote_floor=None,
            exclude_zero_votes=True,
            **{key: value for key, value in kwargs.items()
               if key not in {"vote_floor", "exclude_zero_votes", "last"}})
    except ValueError:
        # Greedy filling can get stuck on sparse vote tables even when a
        # feasible allocation exists. Find a starting flow without optimizing E.
        allocation = _allocate(reference, rows, party_totals, prior, divisors, kwargs,
                               feasibility=True)
        initial = None
    allocation, exchanges = improve_by_exchanges(reference, allocation, prior, divisors=divisors)
    return allocation, {
        "data": {"initial": initial, "exchanges": exchanges},
        "functions": [print_initial, print_improvements],
    }


def improve_by_exchanges(reference, allocation, prior, *, divisors=None):
    allocation = np.asarray(allocation, dtype=int)
    if divisors is None:
        divisors = divisor_values(sainte_lague_gen, int(allocation.sum(axis=1).max(initial=0)))
    reciprocal = np.divide(1., reference, out=np.full_like(reference, np.inf),
                           where=reference > 0)
    return improve_by_costs(allocation, prior, lambda seats: divisors[seats] * reciprocal)


def print_exact(system, data):
    return [], [], None


def print_initial(system, steps):
    initial = steps["initial"]
    if initial is None:
        return [], [], "Initial feasible allocation from network LP"
    headers, rows, _ = print_demo_table(system, initial["data"])
    return headers, rows, "Initial allocation by local fractional-seat quotients"


def print_improvements(system, steps):
    return print_exchanges(
        system, steps, gain_key="reduction",
        gain_title="Objective reduction")
