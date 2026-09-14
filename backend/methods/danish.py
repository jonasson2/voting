"""Danish eligibility, overhang correction and regional preparation."""
import numpy as np

from apportion import apportion1d_general
from methods.max_const_votes import max_const_votes


def fixed_seats(votes, seats, independent, divisor_gen, rng):
    # An independent candidate can win one seat, not a party delegation.
    targets = np.where(independent, 1, seats)
    allocation, demo = max_const_votes(
        [votes], [seats], targets, np.zeros((1, len(votes)), int), divisor_gen,
        num_adjustment_seats=seats, min_adj_seats=[seats], max_adj_seats=[seats],
        exclude_zero_votes=True, rng=rng)
    last = demo["data"][-1]
    return allocation[0], {"idx": last["party"], "active_votes": last["quotient"]}


def eligible_parties(votes, fixed, independent, groups, threshold_totals,
                     threshold=2, seat_threshold=1, threshold_choice=1):
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
    regional_tests = np.zeros(len(national), int)
    for indices in groups:
        seats = int(fixed[indices].sum())
        if seats:
            regional_tests += (
                votes[indices].sum(axis=0) * seats >= threshold_totals[indices].sum())
    return (qualified | (regional_tests >= 2)) & ~independent & (national > 0)


def party_totals(votes, fixed, eligible, total, rule, rule_type, rng):
    """Recalculate mutable t; fixed f and original entitlements stay unchanged."""
    def apportion(active, seats):
        indices = rng.permutation(np.flatnonzero(active))
        result = np.zeros(len(votes), int)
        if seats < 0 or (seats and (not len(indices) or not votes[indices].sum())):
            raise ValueError("No eligible parties can receive the Danish party-seat pool.")
        if seats:
            allocation, _, _ = apportion1d_general(
                votes[indices], seats, [], rule, rule_type)
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
        raise ValueError("Danish overhang correction could not produce feasible party totals.")
    return t


def region_groups(constituencies, regions):
    return [np.array([c for c, const in enumerate(constituencies)
                      if const.get("region") == region["abbreviation"]], dtype=int)
            for region in regions]


def prepare_regions(votes, fixed, totals, regions, groups, divisor_gen, rng):
    regional_votes = np.array([votes[group].sum(axis=0) for group in groups])
    regional_fixed = np.array([fixed[group].sum(axis=0) for group in groups])
    seats = [region["num_adj_seats"] for region in regions]
    try:
        allocated, demo = max_const_votes(
            regional_votes, regional_fixed.sum(axis=1) + seats, totals,
            regional_fixed, divisor_gen, num_adjustment_seats=sum(seats),
            min_adj_seats=seats, max_adj_seats=seats,
            exclude_zero_votes=True, rng=rng)
    except ValueError as error:
        raise ValueError(
            "Danish regional allocation cannot fill the entitlements with the "
            "available votes. The statutory advance-allocation procedure is "
            "not implemented.") from error
    for step in demo["data"]:
        step["region"] = regions[step["constituency"]]["abbreviation"]
    demo["function"] = regional_demo
    return allocated, demo


def allocate_regions(votes, fixed, regional_totals, regions, groups,
                     minimums, maxima, divisor_gen, rng):
    allocated = fixed.copy()
    steps = []
    for r, (region, group) in enumerate(zip(regions, groups)):
        local, demo = max_const_votes(
            votes[group], fixed[group].sum(axis=1) + minimums[group],
            regional_totals[r], fixed[group], divisor_gen,
            num_adjustment_seats=region["num_adj_seats"],
            min_adj_seats=minimums[group], max_adj_seats=[maxima[c] for c in group],
            exclude_zero_votes=True, rng=rng)
        if not np.array_equal(local.sum(axis=0), regional_totals[r]):
            raise RuntimeError("Danish constituency allocation missed its regional party totals.")
        allocated[group] = local
        for step in demo["data"]:
            step["constituency"] = int(group[step["constituency"]])
            step["region"] = region["abbreviation"]
        steps.extend(demo["data"])
    return allocated, {"data": steps, "function": constituency_demo, "format": "cllscc3l"}


def regional_demo(system, steps):
    headers = ["Adjustment seat #", "Region", "Party", "Votes", "Divisor", "Vote score", "Tie"]
    rows = [[i, step["region"], system["parties"][step["party"]],
             step["votes"], step["divisor"], step["quotient"], "Lot" if step["lot"] else ""]
            for i, step in enumerate(steps, 1)]
    return headers, rows, "Allocation of adjustment seats to regions"


def constituency_demo(system, steps):
    headers, rows, _ = regional_demo(system, steps)
    headers.insert(2, "Constituency")
    for row, step in zip(rows, steps):
        row.insert(2, system["constituencies"][step["constituency"]]["name"])
    return headers, rows, "Allocation of adjustment seats to constituencies"
