import numpy as np


def max_const_votes(
        m_votes, v_desired_row_sums, v_desired_col_sums,
        m_prior_allocations, divisor_gen, **kwargs):
    """Allocate a bounded adjustment-seat pool by maximum list quotient."""
    votes = np.asarray(m_votes, dtype=float)
    allocation = np.asarray(m_prior_allocations, dtype=int).copy()
    targets = np.asarray(v_desired_col_sums, dtype=int)
    national_fixed = kwargs.get("nat_prior_allocations")
    if national_fixed is None:
        national_fixed = np.zeros(len(targets), dtype=int)
    else:
        national_fixed = np.asarray(national_fixed, dtype=int)
    deficits = targets - allocation.sum(axis=0) - national_fixed
    if (deficits < 0).any():
        raise ValueError("Adjustment seats cannot resolve a party overhang.")

    total_seats = int(kwargs.get(
        "num_adjustment_seats",
        sum(v_desired_row_sums) - int(allocation.sum()),
    ))
    if int(deficits.sum()) < total_seats:
        raise ValueError(
            "Party deficits are smaller than the adjustment-seat total.")

    nconst, nparty = votes.shape
    minimums = np.asarray(
        kwargs.get("min_adj_seats", [0] * nconst), dtype=int)
    maxima = kwargs.get("max_adj_seats", minimums)
    if len(minimums) != nconst or len(maxima) != nconst:
        raise ValueError("Adjustment-seat bounds do not match the constituencies.")
    if (minimums < 0).any():
        raise ValueError("Adjustment-seat minimums must be non-negative.")
    if int(minimums.sum()) > total_seats:
        raise ValueError(
            "Constituency minimums exceed the adjustment-seat total.")
    capacity = np.array([
        total_seats if maximum is None else int(maximum)
        for maximum in maxima
    ], dtype=int)
    if (capacity < minimums).any():
        raise ValueError(
            "An adjustment-seat maximum is below its constituency minimum.")
    if int(capacity.sum()) < total_seats:
        raise ValueError(
            "Constituency maxima prevent allocation of all adjustment seats.")

    generator = divisor_gen()
    divisors = np.array([
        next(generator) for _ in range(int(allocation.max()) + total_seats + 1)
    ])
    added = np.zeros(nconst, dtype=int)
    steps = []
    for _ in range(total_seats):
        minimum_needed = np.maximum(minimums - added, 0)
        remaining = total_seats - int(added.sum())
        if remaining == int(minimum_needed.sum()):
            open_const = minimum_needed > 0
        else:
            open_const = added < capacity
        open_party = deficits > 0
        scores = np.full((nconst, nparty), -np.inf)
        scores[np.ix_(open_const, open_party)] = (
            votes[np.ix_(open_const, open_party)]
            / divisors[allocation[np.ix_(open_const, open_party)]]
        )
        if kwargs.get("exclude_zero_votes"):
            scores[votes <= 0] = -np.inf
        if not np.isfinite(scores).any():
            raise ValueError("No eligible party-constituency pair can receive the remaining seats.")
        tied = np.flatnonzero(scores == scores.max())
        rng = kwargs.get("rng")
        winner = rng.choice(tied) if rng is not None else tied[0]
        c, p = np.unravel_index(winner, scores.shape)
        quotient = float(scores[c, p])
        divisor = float(divisors[allocation[c, p]])
        allocation[c, p] += 1
        added[c] += 1
        deficits[p] -= 1
        steps.append({
            "constituency": int(c),
            "party": int(p),
            "quotient": quotient,
            "votes": float(votes[c, p]),
            "divisor": divisor,
            "lot": bool(len(tied) > 1 and rng is not None),
        })

    if (added < minimums).any():
        raise RuntimeError("Adjustment-seat allocation did not meet its minimums.")

    return allocation, {"data": steps, "function": print_demo_table}


def print_demo_table(rules, steps):
    headers = [
        "Adjustment seat #", "Constituency", "Party", "Criteria", "Vote score",
    ]
    data = [[
        number,
        rules["constituencies"][step["constituency"]]["name"],
        rules["parties"][step["party"]],
        "Maximum over all eligible lists",
        step["quotient"],
    ] for number, step in enumerate(steps, start=1)]
    return headers, data, "Allocation of adjustment seats"
