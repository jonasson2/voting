"""Fill bounded adjustment seats, then improve by exchanges and seat moves."""

import numpy as np

from common_allocate import prepare_adjustment_bounds
from methods.max_const_votes import max_const_votes, print_demo_table
from methods.switching_plus import improve_by_exchanges, print_exchanges


def switching_flex(votes, row_totals, party_totals, prior, divisor_gen, **kwargs):
    prior = np.asarray(prior, dtype=int)
    base = prior.sum(axis=1)
    minimums, _, capacity = prepare_adjustment_bounds(base, row_totals, kwargs)
    # Use the same logical votes in both phases, as in generic switching.
    votes = np.maximum(np.asarray(votes, dtype=float), 1)
    allocation, initial_demo = max_const_votes(
        votes, row_totals, party_totals, prior, divisor_gen, **kwargs)
    allocation, exchanges = improve_by_exchanges(
        votes, allocation, prior, divisor_gen,
        row_bounds=(base + minimums, base + capacity))
    demo = {
        "data": {"initial": initial_demo["data"], "exchanges": exchanges},
        "functions": [print_initial, print_improvements],
    }
    return allocation, demo


def print_initial(system, steps):
    headers, rows, _ = print_demo_table(system, steps["initial"])
    return headers, rows, "Initial allocation by maximum constituency votes"


def print_improvements(system, steps):
    headers, rows, _ = print_exchanges(system, steps)
    if not steps["exchanges"]:
        rows[0][1] = "No improving exchange or move"
    return headers, rows, "Improving exchanges and moves"
