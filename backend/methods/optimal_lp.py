"""Maximum-entropy adjustment-seat allocation using a network LP."""

import numpy as np
from methods.seat_lp import allocate_by_marginal_costs


def _divisors(divisor_gen, count):
    generator = divisor_gen()
    values = np.array([next(generator) for _ in range(count)], dtype=float)
    if (not np.isfinite(values).all() or (values <= 0).any()
            or (np.diff(values) < 0).any()):
        raise ValueError(
            "Optimal LP requires positive, finite, nondecreasing divisors.")
    return values


def optimal_lp(
        m_votes, v_desired_row_sums, v_desired_col_sums,
        m_prior_allocations, divisor_gen, nat_prior_allocations=None,
        **kwargs):
    """Maximize divisor-rule entropy within row and optional party bounds."""
    votes = np.maximum(np.asarray(m_votes, dtype=float), 1)
    prior = np.asarray(m_prior_allocations, dtype=int)
    if votes.shape != prior.shape:
        raise ValueError("Votes and prior allocations must have the same shape.")

    def costs(variables):
        divisors = _divisors(divisor_gen, max(k for _, _, k in variables) + 1)
        return -np.array([
            np.log(votes[c, p] / divisors[k]) for c, p, k in variables
        ])

    allocation = allocate_by_marginal_costs(
        v_desired_row_sums, v_desired_col_sums, prior, costs,
        nat_prior_allocations=nat_prior_allocations, name="Optimal LP", **kwargs)
    return allocation, {"data": [], "function": print_demo_table}


def print_demo_table(rules, data):
    return [], [], None
