import numpy as np


def max_const_votes(
        votes, target_party_seats, prior_allocations, divisor_gen,
        total_seats, max_per_const=None):
    """Allocate an unassigned seat pool by maximum absolute list quotient."""
    votes = np.asarray(votes, dtype=float)
    allocation = np.asarray(prior_allocations, dtype=int).copy()
    targets = np.asarray(target_party_seats, dtype=int)
    deficits = targets - allocation.sum(axis=0)
    if (deficits < 0).any():
        raise ValueError("Additional seats cannot resolve a party overhang.")
    if int(deficits.sum()) != int(total_seats):
        raise ValueError(
            "Party deficits do not equal the additional adjustment-seat total.")

    nconst, nparty = votes.shape
    if max_per_const is None:
        capacity = np.full(nconst, total_seats, dtype=int)
    else:
        capacity = np.array([
            total_seats if maximum is None else maximum
            for maximum in max_per_const
        ], dtype=int)

    generator = divisor_gen()
    divisors = np.array([
        next(generator) for _ in range(int(allocation.max()) + total_seats + 1)
    ])
    added = np.zeros(nconst, dtype=int)
    steps = []
    while deficits.any():
        open_const = added < capacity
        open_party = deficits > 0
        scores = np.full((nconst, nparty), -np.inf)
        scores[np.ix_(open_const, open_party)] = (
            votes[np.ix_(open_const, open_party)]
            / divisors[allocation[np.ix_(open_const, open_party)]]
        )
        if not np.isfinite(scores).any():
            raise ValueError("Constituency maxima prevent allocation of all seats.")
        c, p = np.unravel_index(np.argmax(scores), scores.shape)
        quotient = float(scores[c, p])
        allocation[c, p] += 1
        added[c] += 1
        deficits[p] -= 1
        steps.append({
            "constituency": int(c),
            "party": int(p),
            "quotient": quotient,
        })

    return allocation, {"data": steps, "function": print_demo_table}


def print_demo_table(rules, steps):
    headers = [
        "Additional seat #", "Constituency", "Party", "Criteria", "Vote score",
    ]
    data = [[
        number,
        rules["constituencies"][step["constituency"]]["name"],
        rules["parties"][step["party"]],
        "Maximum over all eligible lists",
        step["quotient"],
    ] for number, step in enumerate(steps, start=1)]
    return headers, data, "Allocation of additional adjustment seats"
