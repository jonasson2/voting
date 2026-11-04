"""Shared local improvement for separable seat objectives."""

from itertools import combinations

import numpy as np

MIN_GAIN = 1e-12


def improve_by_costs(allocation, prior, marginal_costs, *, row_bounds=None,
                     gain_key="reduction"):
    """Choose the best reciprocal exchange or, with flexible bounds, seat move."""
    allocation = np.asarray(allocation, dtype=int).copy()
    prior = np.asarray(prior, dtype=int)
    rows = allocation.sum(axis=1)
    lower, upper = (rows, rows) if row_bounds is None else row_bounds
    lower, upper = np.asarray(lower), np.asarray(upper)
    parties = allocation.sum(axis=0)
    exchanges = []

    while True:
        incoming = -marginal_costs(allocation)
        outgoing = -marginal_costs(np.maximum(allocation - 1, 0))
        donors = [np.flatnonzero(row > fixed)
                  for row, fixed in zip(allocation, prior)]
        best_gain, best_exchange = find_best_exchange(incoming, outgoing, donors)
        move_gain, move = _best_move(
            incoming, outgoing, donors, rows, lower, upper)
        if move_gain > best_gain:
            best_gain, best_exchange = move_gain, move
        if best_exchange is None:
            break
        c, d, p, q = best_exchange
        allocation[c, p] -= 1
        allocation[d, p] += 1
        if q is None:
            rows[c] -= 1
            rows[d] += 1
        else:
            allocation[d, q] -= 1
            allocation[c, q] += 1
        exchanges.append({
            "from_constituency": c, "to_constituency": d,
            "from_party": p, "to_party": q, gain_key: best_gain,
        })

    if ((allocation < prior).any()
            or (allocation.sum(axis=1) < lower).any()
            or (allocation.sum(axis=1) > upper).any()
            or not np.array_equal(allocation.sum(axis=0), parties)):
        raise RuntimeError("Internal switching error: improvement violated seat constraints.")
    return allocation, exchanges


def find_best_exchange(incoming, outgoing, donors):
    """Find the reciprocal exchange with the greatest additive gain."""
    best_gain, best = MIN_GAIN, None
    for c, d in combinations(range(len(donors)), 2):
        p, q = donors[c], donors[d]
        if not len(p) or not len(q):
            continue
        # p moves from c to d; q moves from d to c.
        gains = ((incoming[d, p] - outgoing[c, p])[:, None]
                 + (incoming[c, q] - outgoing[d, q])[None, :])
        gains[p[:, None] == q[None, :]] = -np.inf
        i, j = np.unravel_index(np.argmax(gains), gains.shape)
        if gains[i, j] > best_gain:
            best_gain = float(gains[i, j])
            best = c, d, int(p[i]), int(q[j])
    return best_gain, best


def _best_move(incoming, outgoing, donors, rows, lower, upper):
    best_gain, best = MIN_GAIN, None
    destinations = np.flatnonzero(rows < upper)
    for c in np.flatnonzero(rows > lower):
        parties = donors[c]
        for d in destinations:
            if c == d or not len(parties):
                continue
            gains = incoming[d, parties] - outgoing[c, parties]
            i = int(np.argmax(gains))
            if gains[i] > best_gain:
                best_gain = float(gains[i])
                best = int(c), int(d), int(parties[i]), None
    return best_gain, best


def print_exchanges(system, steps, *, gain_key="log_gain",
                    gain_title="Entropy improvement"):
    headers = ["No.", "Constituency 1", "From", "To",
               "Constituency 2", "From", "To", gain_title]
    rows = [[
        number,
        system["constituencies"][step["from_constituency"]]["name"],
        system["parties"][step["from_party"]],
        system["parties"][step["to_party"]] if step["to_party"] is not None else "-",
        system["constituencies"][step["to_constituency"]]["name"],
        system["parties"][step["to_party"]] if step["to_party"] is not None else "-",
        system["parties"][step["from_party"]],
        step[gain_key],
    ] for number, step in enumerate(steps["exchanges"], 1)]
    if not rows:
        rows = [["-", "No improving exchange", "-", "-", "-", "-", "-", "-"]]
    return headers, rows, "Improving exchanges"
