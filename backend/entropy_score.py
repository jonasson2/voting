"""Rule-specific entropy score for final adjustment-seat allocations."""

from math import exp
import numpy as np

from methods import regional
from methods.optimal_lp import optimal_lp
from table_util import entropy


UNSUPPORTED_RULES = {"adams", "huntington-hill"}
METHODS_WITHOUT_PARTY_TARGETS = {
    "adjustment-as-fixed", "party-seats-unbounded",
}
SCORE_TOLERANCE = 1e-8


def is_available(election):
    """Return whether the final divider has a rigorous finite score."""
    return election.system["adj_alloc_divider"] not in UNSUPPORTED_RULES


def _array_key(values):
    array = np.ascontiguousarray(np.asarray(values))
    return array.shape, array.dtype.str, array.tobytes()


def _problem_key(election):
    """Identify an LP objective and feasible set within one vote draw."""
    enforce_party_targets = (
        election.system["adjustment_method"]
        not in METHODS_WITHOUT_PARTY_TARGETS)
    national_fixed = (
        election.results["fixed_nat_seats"]
        if election.party_vote_info["specified"] else [])
    regional_totals = (
        election.region_party_totals if election.has_regions else [])
    return (
        election.system["adj_alloc_divider"],
        enforce_party_targets,
        _array_key(election.votes),
        _array_key(election.prepared_const_seats),
        _array_key(election.desired_row_sums),
        _array_key(election.desired_col_sums if enforce_party_targets else []),
        election.num_adjustment_seats,
        tuple(int(value) for value in election.min_adj_seats),
        tuple(-1 if value is None else int(value)
              for value in election.max_adj_seats),
        _array_key(national_fixed),
        _array_key(regional_totals),
        tuple(tuple(int(index) for index in group)
              for group in getattr(election, "region_groups", [])),
    )


def _optimal_allocation(election, divisor_gen, enforce_party_targets):
    if election.has_regions:
        allocation, _ = regional.allocate_within_regions(
            election.votes,
            election.prepared_const_seats,
            election.region_party_totals,
            election.regions,
            election.region_groups,
            election.min_adj_seats,
            election.max_adj_seats,
            divisor_gen,
            rng=None,
            method=optimal_lp,
            method_name="optimal-lp",
        )
        return allocation

    national_fixed = (
        election.results["fixed_nat_seats"]
        if election.party_vote_info["specified"] else None)
    allocation, _ = optimal_lp(
        election.votes,
        election.desired_row_sums,
        election.desired_col_sums,
        election.prepared_const_seats,
        divisor_gen,
        nat_prior_allocations=national_fixed,
        num_adjustment_seats=election.num_adjustment_seats,
        min_adj_seats=election.min_adj_seats,
        max_adj_seats=election.max_adj_seats,
        enforce_party_targets=enforce_party_targets,
    )
    return allocation


def calculate(election, optimum_cache=None):
    """Return the allocation's product score relative to its optimum."""
    if not is_available(election):
        return None

    cache = optimum_cache if optimum_cache is not None else {}
    key = _problem_key(election)
    divisor_gen = election.system.get_generator("adj_alloc_divider")
    logical_votes = np.maximum(np.asarray(election.votes, dtype=float), 1)
    actual = entropy(
        logical_votes, election.results["all_const_seats"], divisor_gen)

    if key not in cache:
        if (election.system["adjustment_method"] == "optimal-lp"
                or election.num_adjustment_seats == 0):
            cache[key] = actual
        else:
            enforce_party_targets = (
                election.system["adjustment_method"]
                not in METHODS_WITHOUT_PARTY_TARGETS)
            optimum = _optimal_allocation(
                election, divisor_gen, enforce_party_targets)
            cache[key] = entropy(logical_votes, optimum, divisor_gen)

    difference = cache[key] - actual
    if difference < -SCORE_TOLERANCE:
        raise RuntimeError(
            "Allocation has a better entropy value than its computed optimum.")
    return exp(-max(difference, 0))
