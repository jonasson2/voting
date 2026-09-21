"""Adjustment-seat switching using Swedish-style excess-seat reassignment."""

import numpy as np

from allocate_pool import next_quotient, quotient_scores
from common_allocate import common_allocate, prepare_adjustment_bounds
from methods.excess_reassignment import reassign_excess, remove_excess
from methods.provisional_allocation import (
    allocate_bounded_provisionally, allocate_provisionally)
from methods.switching_tables import print_initial_allocation, print_reassignment_table


def switching(m_votes, v_desired_row_sums, v_desired_col_sums,
              m_prior_allocations, divisor_gen, **kwargs):
    prior = np.asarray(m_prior_allocations, dtype=int)
    base = prior.sum(axis=1)
    minimums = np.asarray(
        kwargs.get(
            "min_adj_seats", np.asarray(v_desired_row_sums) - base),
        dtype=int,
    )
    total = int(kwargs.get("num_adjustment_seats", minimums.sum()))
    if total > int(minimums.sum()):
        return switching_with_bounds(
            m_votes, v_desired_row_sums, v_desired_col_sums,
            m_prior_allocations, divisor_gen, **kwargs)
    return switching_fixed(
        m_votes, v_desired_row_sums, v_desired_col_sums,
        m_prior_allocations, divisor_gen, **kwargs)


def switching_fixed(m_votes, v_desired_row_sums, v_desired_col_sums,
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


def switching_with_bounds(m_votes, v_desired_row_sums, v_desired_col_sums,
                          m_prior_allocations, divisor_gen, **kwargs):
    """Return excess seats to a shared pool and reallocate within row bounds."""
    votes = np.maximum(np.asarray(m_votes, dtype=float), 1)
    prior = np.asarray(m_prior_allocations, dtype=int)
    party_totals = np.asarray(v_desired_col_sums, dtype=int)
    base = prior.sum(axis=1)
    if (prior.sum(axis=0) > party_totals).any():
        raise ValueError("Protected fixed seats exceed a party's seat target.")
    minimums, total, capacity = prepare_adjustment_bounds(
        base, v_desired_row_sums, kwargs)
    if int((party_totals - prior.sum(axis=0)).sum()) < total:
        raise ValueError("Party deficits are smaller than the adjustment-seat total.")

    initial, _ = allocate_bounded_provisionally(
        votes, base + minimums, base + capacity, party_totals, prior,
        divisor_gen, total - int(minimums.sum()),
        rng=kwargs.get("rng"), on_tie=kwargs.get("on_tie"))
    reduced, removals = remove_excess(
        votes, initial, party_totals, divisor_gen,
        removable_floor=prior,
        removable_rows=np.ones(prior.shape[0], dtype=bool),
        on_tie=kwargs.get("on_tie"),
        rng=kwargs.get("rng"),
    )

    current = reduced.sum(axis=1) - base
    required = np.maximum(minimums - current, 0)
    remaining_capacity = capacity - current
    allocation, refill_demo = common_allocate(
        votes,
        reduced.sum(axis=1) + required,
        party_totals,
        reduced,
        divisor_gen,
        next_quotient,
        "Vote score",
        "Maximum quotient among parties below their target",
        flex_scores=quotient_scores,
        vote_floor=None,
        num_adjustment_seats=len(removals),
        min_adj_seats=required,
        max_adj_seats=remaining_capacity,
        rng=kwargs.get("rng"),
        on_tie=kwargs.get("on_tie"),
    )

    added = allocation.sum(axis=1) - base
    if (int(added.sum()) != total or (added < minimums).any()
            or (added > capacity).any() or (allocation < prior).any()
            or (allocation.sum(axis=0) > party_totals).any()):
        raise RuntimeError(
            "Internal Swedish-style switching error: seat constraints violated.")

    steps = {
        "initial_allocation": [
            {"party": p, "goal": int(goal),
             "actual": int(initial[:, p].sum())}
            for p, goal in enumerate(party_totals)
        ],
        "removals": removals,
        "reallocations": refill_demo["data"]["sequence"],
    }
    return allocation, {
        "data": steps,
        "function": print_initial_allocation,
        "functions": [
            print_initial_allocation,
            print_removal_table,
            print_reallocation_table,
        ],
        "format": ("sccc", "cll3", "clls3"),
    }


def print_removal_table(rules, steps):
    headers = ["No.", "Constituency", "From", "Returned quotient"]
    data = [[
        number,
        rules["constituencies"][removal["constituency"]]["name"],
        rules["parties"][removal["from"]],
        removal["removal_quotient"],
    ] for number, removal in enumerate(steps["removals"], start=1)]
    if not data:
        data = [["–", "–", "No excess seats", "–"]]
    return headers, data, "Removal of excess adjustment seats"


def print_reallocation_table(rules, steps):
    headers = ["No.", "Constituency", "To", "Criteria", "Recipient quotient"]
    data = [[
        number,
        rules["constituencies"][seat["constituency"]]["name"],
        rules["parties"][seat["party"]],
        seat["reason"],
        seat["quotient"],
    ] for number, seat in enumerate(steps["reallocations"], start=1)]
    if not data:
        data = [["–", "–", "No reallocation required", "–", "–"]]
    return headers, data, "Reallocation of returned adjustment seats"
