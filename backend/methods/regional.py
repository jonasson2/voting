"""Allocation of adjustment seats first to regions, then to constituencies."""

import numpy as np

from methods.max_const_votes import max_const_votes
from ties import remap


def region_groups(constituencies, regions):
    return [
        np.array([
            c for c, constituency in enumerate(constituencies)
            if constituency.get("region") == region["abbreviation"]
        ], dtype=int)
        for region in regions
    ]


def allocate_to_regions(votes, fixed, totals, regions, groups, divisor_gen,
                        rng, on_tie=None, method=max_const_votes,
                        method_name="max-const-votes"):
    """Distribute party entitlements among regions with exact regional totals."""
    regional_votes = np.array([votes[group].sum(axis=0) for group in groups])
    regional_fixed = np.array([fixed[group].sum(axis=0) for group in groups])
    seats = np.array([region["num_adj_seats"] for region in regions], dtype=int)
    try:
        allocated, demo = method(
            regional_votes,
            regional_fixed.sum(axis=1) + seats,
            totals,
            regional_fixed,
            divisor_gen,
            num_adjustment_seats=int(seats.sum()),
            min_adj_seats=seats,
            max_adj_seats=seats,
            exclude_zero_votes=True,
            rng=rng,
            on_tie=on_tie,
        )
    except ValueError as error:
        raise ValueError(
            "Regional allocation cannot fill the party entitlements with the "
            "available votes. A required advance-allocation procedure is not "
            "implemented."
        ) from error

    allocated = np.asarray(allocated, dtype=int)
    expected_rows = regional_fixed.sum(axis=1) + seats
    if (not np.array_equal(allocated.sum(axis=0), totals)
            or not np.array_equal(allocated.sum(axis=1), expected_rows)):
        raise RuntimeError("Regional allocation did not satisfy its margins.")

    if method_name == "max-const-votes":
        for step in demo["data"]:
            step["region"] = regions[step["constituency"]]["abbreviation"]
        demo["function"] = regional_demo
        demo["format"] = "clscc3l"
    else:
        demo["constituencies"] = [
            {"name": region["name"]} for region in regions
        ]
        demo["scope"] = "region"
    return allocated, demo


def _remap_demo_constituencies(value, group, key=None):
    """Translate constituency indices in a regional method demonstration."""
    constituency_keys = {
        "constituency", "from_constituency", "to_constituency",
    }
    if key in constituency_keys and isinstance(value, (int, np.integer)):
        return int(group[value])
    if isinstance(value, dict):
        return {
            item_key: _remap_demo_constituencies(item, group, item_key)
            for item_key, item in value.items()
        }
    if isinstance(value, list):
        return [_remap_demo_constituencies(item, group) for item in value]
    return value


def allocate_within_regions(votes, fixed, regional_totals, regions, groups,
                            minimums, maxima, divisor_gen, rng, on_tie=None,
                            method=max_const_votes,
                            method_name="max-const-votes"):
    """Apply the selected constituency allocator independently in each region."""
    allocated = fixed.copy()
    steps = []
    stages = []
    for r, (region, group) in enumerate(zip(regions, groups)):
        local_on_tie = (
            remap(on_tie, (group[:, None] * votes.shape[1]
                           + np.arange(votes.shape[1])).ravel())
            if on_tie is not None else None)
        local, demo = method(
            votes[group], fixed[group].sum(axis=1) + minimums[group],
            regional_totals[r], fixed[group], divisor_gen,
            num_adjustment_seats=region["num_adj_seats"],
            min_adj_seats=minimums[group],
            max_adj_seats=[maxima[c] for c in group],
            exclude_zero_votes=True, rng=rng,
            on_tie=local_on_tie)
        if not np.array_equal(local.sum(axis=0), regional_totals[r]):
            raise RuntimeError(
                "Constituency allocation missed its regional party totals.")
        added = local.sum(axis=1) - fixed[group].sum(axis=1)
        capacities = np.array([
            region["num_adj_seats"] if maxima[c] is None else maxima[c]
            for c in group
        ])
        if (int(added.sum()) != region["num_adj_seats"]
                or (added < minimums[group]).any()
                or (added > capacities).any()):
            raise RuntimeError(
                "Constituency allocation violated constituency bounds.")
        allocated[group] = local
        if method_name == "max-const-votes":
            for step in demo["data"]:
                step["constituency"] = int(group[step["constituency"]])
                step["region"] = region["abbreviation"]
            steps.extend(demo["data"])
        else:
            stages.append({
                "demo": _remap_demo_constituencies(demo, group),
                "title_prefix": region["name"],
            })
    if method_name == "max-const-votes":
        return allocated, {
            "data": steps,
            "function": constituency_demo,
            "format": "cllscc3l",
        }
    return allocated, {"stages": stages}


def regional_demo(system, steps):
    headers = [
        "Adjustment seat #", "Region", "Party", "Votes", "Divisor",
        "Vote score", "Tie",
    ]
    rows = [[
        i, step["region"], system["parties"][step["party"]],
        step["votes"], step["divisor"], step["quotient"],
        "Lot" if step["lot"] else "First in table" if step["tie"] else "",
    ] for i, step in enumerate(steps, 1)]
    return headers, rows, "Regional allocation of adjustment seats"


def constituency_demo(system, steps):
    headers, rows, _ = regional_demo(system, steps)
    headers.insert(2, "Constituency")
    for row, step in zip(rows, steps):
        row.insert(2, system["constituencies"][step["constituency"]]["name"])
    return headers, rows, "Allocation of adjustment seats to constituencies"
