"""Greedy one-way corrections, optionally improved within the same list bounds."""

from functools import partial

import numpy as np

from methods.constituency_optimal import prepare_baseline
from methods.provisional_allocation import divisor_values
from methods.seat_switching import find_best_exchange, print_exchanges
from methods.switching import print_demo_table2
from methods.switching_tables import print_initial_allocation


def allocate(votes, row_totals, party_totals, prior, divisor_gen, *,
             rectangles=True, **kwargs):
    prior = np.asarray(prior, dtype=int)
    votes, rows, targets, baseline = prepare_baseline(
        votes, row_totals, party_totals, prior, divisor_gen, kwargs)
    allocation = baseline.copy()
    difference = baseline.sum(axis=0) - targets
    over, under = difference > 0, difference < 0
    lower = np.where(over[None, :], prior, baseline)
    upper = np.where(under[None, :], rows[:, None], baseline)
    divisors = divisor_values(divisor_gen, int(rows.max(initial=0)) + 1)
    log_votes = np.log(votes)
    log_divisors = np.log(divisors)
    steps = {
        "initial_allocation": [
            {"party": p, "goal": int(targets[p]), "actual": int(actual)}
            for p, actual in enumerate(baseline.sum(axis=0))],
        "switches": [], "exchanges": [],
    }

    while (allocation.sum(axis=0) != targets).any():
        balance = allocation.sum(axis=0) - targets
        outgoing = log_votes - log_divisors[np.maximum(allocation - 1, 0)]
        incoming = log_votes - log_divisors[allocation]
        outgoing[(allocation <= lower) | (balance <= 0)[None, :]] = np.inf
        incoming[:, balance >= 0] = -np.inf
        donors, recipients = outgoing.argmin(axis=1), incoming.argmax(axis=1)
        c = np.arange(len(rows))
        gains = incoming[c, recipients] - outgoing[c, donors]
        constituency = int(np.argmax(gains))
        if not np.isfinite(gains[constituency]):
            raise RuntimeError("No one-way transfer can satisfy party targets.")
        p, q = int(donors[constituency]), int(recipients[constituency])
        allocation[constituency, p] -= 1
        allocation[constituency, q] += 1
        steps["switches"].append({
            "constituency": constituency, "from": p, "to": q,
            "ratio": float(np.exp(-gains[constituency])),
        })

    # The baseline bounds allow O–U, O–O and U–U pairs; E lists stay fixed.
    while rectangles:
        incoming = log_votes - log_divisors[allocation]
        incoming[allocation >= upper] = -np.inf
        outgoing = log_votes - log_divisors[np.maximum(allocation - 1, 0)]
        donors = [np.flatnonzero(row > bound)
                  for row, bound in zip(allocation, lower)]
        gain, exchange = find_best_exchange(incoming, outgoing, donors)
        if exchange is None:
            break
        c, d, p, q = exchange
        allocation[c, p] -= 1
        allocation[d, p] += 1
        allocation[d, q] -= 1
        allocation[c, q] += 1
        steps["exchanges"].append({
            "from_constituency": c, "to_constituency": d,
            "from_party": p, "to_party": q, "log_gain": gain,
        })

    if ((allocation < lower).any() or (allocation > upper).any()
            or not np.array_equal(allocation.sum(axis=0), targets)
            or not np.array_equal(allocation.sum(axis=1), rows)):
        raise RuntimeError("One-way switching violated seat constraints.")
    functions = [print_initial_allocation, print_demo_table2]
    if rectangles:
        functions.append(print_exchanges)
    return allocation, {"data": steps, "functions": functions}


one_way_switching = partial(allocate, rectangles=True)
simple_one_way_switching = partial(allocate, rectangles=False)
