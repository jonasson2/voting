import numpy as np
from methods.excess_reassignment import reassign_excess
from methods.switching_tables import print_reassignment_table


def _eligible(shares, threshold):
    return shares * 100 >= threshold


def switching(
        m_votes, v_desired_row_sums, v_desired_col_sums,
        m_prior_allocations, divisor_gen, **kwargs):
    """Return excess seats and reassign them within their constituencies."""
    votes = np.asarray(m_votes, dtype=float)
    row_totals = np.asarray(v_desired_row_sums, dtype=int)
    party_totals = np.asarray(v_desired_col_sums, dtype=int)
    prior = np.asarray(m_prior_allocations, dtype=int)
    if not np.array_equal(prior.sum(axis=1), row_totals):
        raise ValueError(
            "Swedish switching requires a complete constituency-seat allocation.")

    nat_votes = np.asarray(kwargs.get("nat_votes", votes.sum(axis=0)), dtype=float)
    nat_threshold_total = kwargs.get("nat_threshold_total", nat_votes.sum())
    const_threshold_totals = np.asarray(
        kwargs.get("const_threshold_totals", votes.sum(axis=1)), dtype=float)
    national_threshold = kwargs.get("national_threshold", 0)
    local_threshold = kwargs.get("local_threshold", 0)

    national_shares = (
        nat_votes / nat_threshold_total
        if nat_threshold_total else np.zeros_like(nat_votes)
    )
    nationally_eligible = _eligible(national_shares, national_threshold)
    local_shares = np.divide(
        votes,
        const_threshold_totals[:, None],
        out=np.zeros_like(votes),
        where=const_threshold_totals[:, None] != 0,
    )
    list_eligible = nationally_eligible[None, :] | _eligible(
        local_shares, local_threshold)

    allocation, switches = reassign_excess(
        votes, prior, party_totals, divisor_gen,
        removable_floor=np.zeros_like(prior),
        eligible=list_eligible,
        removable_rows=row_totals >= 3,
        on_tie=kwargs.get("on_tie"),
    )

    stepbystep = {
        "data": {"switches": switches},
        "function": print_reassignment_table,
        "party_totals": party_totals,
        "seat_changes": allocation - prior,
    }
    return allocation, stepbystep
