"""Danish fixed-seat, eligibility and party-total rules."""
import numpy as np

from apportion import apportion1d_general
from methods.max_const_votes import max_const_votes
from randomness import random_permutation
from ties import remap


def fixed_seats(votes, seats, independent, divisor_gen, rng, on_tie=None):
    # An independent candidate can win one seat, not a party delegation.
    targets = np.where(independent, 1, seats)
    allocation, demo = max_const_votes(
        [votes], [seats], targets, np.zeros((1, len(votes)), int), divisor_gen,
        num_adjustment_seats=seats, min_adj_seats=[seats], max_adj_seats=[seats],
        exclude_zero_votes=True, rng=rng, on_tie=on_tie)
    last = demo["data"][-1]
    return allocation[0], {"idx": last["party"], "active_votes": last["quotient"]}


def eligible_parties(votes, fixed, independent, groups, threshold_totals,
                     threshold=2, seat_threshold=1, threshold_choice=1,
                     two_region_qualification=True):
    national = votes.sum(axis=0)
    total = threshold_totals.sum()
    percent_test = (national > 0) & (national * 100 >= threshold * total)
    seat_test = fixed.sum(axis=0) >= seat_threshold
    if seat_threshold == 0:
        qualified = percent_test
    elif threshold_choice == 1:
        qualified = percent_test | seat_test
    else:
        qualified = percent_test & seat_test
    if two_region_qualification:
        regional_tests = np.zeros(len(national), int)
        for indices in groups:
            seats = int(fixed[indices].sum())
            if seats:
                regional_tests += (
                    votes[indices].sum(axis=0) * seats >= threshold_totals[indices].sum())
        qualified |= regional_tests >= 2
    return qualified & ~independent & (national > 0)


def party_totals(votes, fixed, eligible, total, rule, rule_type, rng, on_tie=None):
    """Recalculate mutable t; fixed f and original entitlements stay unchanged."""
    def apportion(active, seats):
        active_indices = np.flatnonzero(active)
        indices = (active_indices[random_permutation(rng, len(active_indices))]
                   if rng is not None else active_indices)
        result = np.zeros(len(votes), int)
        if seats < 0 or (seats and (not len(indices) or not votes[indices].sum())):
            raise ValueError("No eligible parties can receive the Danish party-seat pool.")
        if seats:
            allocation, _, _ = apportion1d_general(
                votes[indices], seats, [], rule, rule_type,
                on_tie=remap(on_tie, indices))
            result[indices] = allocation
        return result

    f = np.asarray(fixed, dtype=int)
    protected = np.where(eligible, 0, f)
    pool = total - int(protected.sum())
    original = apportion(eligible, pool)
    t = original + protected
    if not np.any(eligible & (f > t)):
        return t
    active = eligible & (f < t)
    t[~active] = f[~active]
    while active.any():
        recalculated = apportion(active, total - int(t[~active].sum()))
        t[active] = recalculated[active]
        capped = active & (t > original)
        if not capped.any():
            break
        t[capped] = original[capped]
        active[capped] = False
    if int(t.sum()) != total or (t < f).any():
        raise ValueError("Danish party-total recalculation could not produce feasible totals.")
    return t


def party_totals_from_fixed(votes, fixed, eligible, total, rule, rule_type,
                            retained_votes, rng, on_tie=None):
    """Keep fixed seats and apportion only the remaining seats to eligible parties."""
    votes = np.asarray(votes)
    fixed = np.asarray(fixed, dtype=int)
    eligible = np.asarray(eligible, dtype=bool)
    totals = fixed.copy()
    pool = total - int(fixed[~eligible].sum())
    remaining = pool - int(fixed[eligible].sum())
    if remaining < 0:
        raise ValueError("Fixed seats exceed the Danish party-seat pool.")
    if remaining == 0:
        return totals

    indices = np.flatnonzero(eligible)
    if not len(indices) or not votes[indices].sum():
        raise ValueError("No eligible parties can receive the Danish party-seat pool.")
    if rng is not None:
        indices = indices[random_permutation(rng, len(indices))]
    allocation, _, _ = apportion1d_general(
        votes[indices], pool, fixed[indices], rule, rule_type,
        threshold_total=votes[indices].sum() + retained_votes,
        on_tie=remap(on_tie, indices))
    totals[indices] = allocation
    return totals
