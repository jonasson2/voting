"""Adjustment-seat switching using Swedish-style excess-seat reassignment."""

import numpy as np

from methods.excess_reassignment import reassign_excess
from methods.provisional_allocation import allocate_provisionally
from methods.switching_tables import print_initial_allocation, print_reassignment_table


def switching(m_votes, v_desired_row_sums, v_desired_col_sums,
              m_prior_allocations, divisor_gen, **kwargs):
    votes = np.maximum(np.asarray(m_votes, dtype=float), 1)
    prior = np.asarray(m_prior_allocations, dtype=int)
    party_totals = np.asarray(v_desired_col_sums, dtype=int)
    initial = allocate_provisionally(
        votes, v_desired_row_sums, party_totals, prior, divisor_gen,
        kwargs.get("on_tie"))
    allocation, switches = reassign_excess(
        votes, initial, party_totals, divisor_gen,
        removable_floor=prior,
        eligible=np.ones_like(prior, dtype=bool),
        removable_rows=np.ones(prior.shape[0], dtype=bool),
        on_tie=kwargs.get("on_tie"),
        rng=kwargs.get("rng"),
    )
    steps = {
        "initial_allocation": [
            {"party": p, "goal": int(goal), "actual": int(initial[:, p].sum())}
            for p, goal in enumerate(party_totals)
        ],
        "switches": switches,
        "title": "Swedish-style switching of adjustment seats",
    }
    return allocation, {
        "data": steps,
        "function": print_initial_allocation,
        "functions": [print_initial_allocation, print_reassignment_table],
    }
