import numpy as np
from common_allocate import prepare_adjustment_bounds
from methods.provisional_allocation import (
    allocate_bounded_provisionally, allocate_provisionally, divisor_values)
from methods.switching_tables import print_initial_allocation

def min_with_index(x, I=None):
    if I is None:
        i = np.argmin(x)
    else:
        i = np.argmin(np.where(I, x, np.inf))
    return (x[i], i)

def max_with_index(x, I=None):
    if I is None:
        i = np.argmax(x)
    else:
        i = np.argmax(np.where(I, x, -np.inf))
    return (x[i], i)

def switching(m_votes, v_desired_row_sums, v_desired_col_sums,
              m_prior_allocations, divisor_gen, **kwargs):
    """Use bounded switching only when a shared adjustment pool exists."""
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


def _divisors(divisor_gen, count):
    return divisor_values(divisor_gen, count)


def switching_fixed(m_votes,
                    v_desired_row_sums,
                    v_desired_col_sums,
                    m_prior_allocations,
                    divisor_gen,
                    **kwargs):

    # CREATE NUMPY ARRAYS AND COUNTS FROM PARAMETER LISTS
    # This generic method treats every constituency-party cell as available.
    votes = np.maximum(np.asarray(m_votes, dtype=float), 1)
    alloc_prior = np.array(m_prior_allocations)
    desired_const = np.array(v_desired_row_sums)
    max_party = np.array(v_desired_col_sums)
    num_constituencies = len(v_desired_row_sums)
    num_parties        = len(v_desired_col_sums)
    if (alloc_prior.sum(axis=1) > desired_const).any():
        raise ValueError("Protected fixed seats exceed a constituency's seat total.")
    if (alloc_prior.sum(axis=0) > max_party).any():
        raise ValueError("Protected fixed seats exceed a party's seat target.")

    # CALCULATE DIVISORS
    N = max(max(desired_const), max(max_party)) + 1
    divisors = _divisors(divisor_gen, N)
    
    # ALLOCATE ADJUSTMENT SEATS AS IF THEY WERE FIXED SEATS
    alloc = allocate_provisionally(
        votes, desired_const, max_party, alloc_prior, divisor_gen)

    # INFORMATION FOR FIRST STEP-BY-STEP DEMO TABLE
    initial_allocation = [{
        "party": p,
        "goal": int(max_party[p]),
        "actual": int(sum(alloc[:,p]))
    } for p in range(num_parties)]

    # WHILE SOME PARTIES HAVE TOO MANY SEATS DO SWITCHING
    switches = []
    while True:
        surplus = sum(alloc,0) > max_party
        if not any(surplus):
            break
        wanting = sum(alloc,0) < max_party

        # CALCULATE MINIMUM RATIO OF ACTIVE VOTES IN EACH CONSTITUENCY
        P = []
        Q = []
        C = []
        ratio = []
        for c in range(num_constituencies):
            with_seats = alloc[c,:] > alloc_prior[c,:]
            with_votes = votes[c,:] > 0
            score = np.zeros(num_parties)
            S = surplus & with_seats
            W = wanting & with_votes
            score[S] = votes[c, S]/divisors[alloc[c, S] - 1]
            score[W] = votes[c, W]/divisors[alloc[c, W]]
            if any(S) and any(W):
                (min_score, p) = min_with_index(score, S)
                (max_score, q) = max_with_index(score, W)
                # Provisional allocation establishes this ordering; removing
                # surplus seats and adding deficit seats can only strengthen it.
                if not min_score >= max_score:
                    raise RuntimeError("Internal switching error: quotient ordering violated.")
                C.append(c)
                P.append(p)
                Q.append(q)
                ratio.append(min_score/max_score)

        # FIND THE SMALLEST RATIO AND SWITCH WITHIN THE CORRESPONDING CONSTITUENCY
        if not C:
            raise RuntimeError("Internal switching error: no switch available for a surplus party.")
        cmin = np.argmin(ratio)
        alloc[C[cmin], P[cmin]] -= 1
        alloc[C[cmin], Q[cmin]] += 1
        switches.append({
            "constituency": C[cmin],
            "from": P[cmin],
            "to": Q[cmin],
            "ratio": ratio[cmin]
            })

    # Party targets can include seats reserved for national allocation.
    if (not np.array_equal(alloc.sum(axis=1), desired_const)
            or (alloc < alloc_prior).any()
            or (alloc.sum(axis=0) > max_party).any()):
        raise RuntimeError("Internal switching error: seat constraints violated.")

    # INFORMATION FOR SECOND STEP-BY-STEP DEMO TABLE
    steps = {
        "initial_allocation": initial_allocation,
        "switches": switches,
    }

    stepbystep = {
        "data": steps,
        "function": print_initial_allocation,
        "functions": [print_initial_allocation, print_demo_table2],
    }
    return alloc, stepbystep


def _switch_globally(
        votes, initial, party_targets, prior, divisors, minimums, capacity):
    allocation = initial.copy()
    base = prior.sum(axis=1)
    added = allocation.sum(axis=1) - base
    switches = []
    while True:
        surplus = allocation.sum(axis=0) > party_targets
        if not surplus.any():
            break
        wanting = allocation.sum(axis=0) < party_targets
        recipient_scores = votes / divisors[allocation]
        recipient_scores[:, ~wanting] = -np.inf
        open_rows = added < capacity

        best = None
        removable = np.argwhere(
            (allocation > prior) & surplus[np.newaxis, :])
        for c, p in removable:
            allowed_rows = open_rows.copy() if added[c] > minimums[c] \
                else np.zeros(len(added), dtype=bool)
            allowed_rows[c] = True
            scores = np.where(
                allowed_rows[:, np.newaxis], recipient_scores, -np.inf)
            if not np.isfinite(scores).any():
                continue
            d, q = np.unravel_index(np.argmax(scores), scores.shape)
            removal = votes[c, p] / divisors[allocation[c, p] - 1]
            recipient = scores[d, q]
            candidate = (removal / recipient, int(c), int(p), int(d), int(q))
            if best is None or candidate < best:
                best = candidate

        if best is None:
            raise RuntimeError(
                "Internal switching error: no bounded switch available for "
                "a surplus party.")
        ratio, c, p, d, q = best
        allocation[c, p] -= 1
        allocation[d, q] += 1
        if c != d:
            added[c] -= 1
            added[d] += 1
        switches.append({
            "from_constituency": c,
            "from": p,
            "to_constituency": d,
            "to": q,
            "ratio": ratio,
        })
    return allocation, switches


def switching_with_bounds(m_votes, v_desired_row_sums, v_desired_col_sums,
                          m_prior_allocations, divisor_gen, **kwargs):
    """Switch seats globally while respecting constituency seat ranges."""
    votes = np.maximum(np.asarray(m_votes, dtype=float), 1)
    prior = np.asarray(m_prior_allocations, dtype=int)
    party_targets = np.asarray(v_desired_col_sums, dtype=int)
    base = prior.sum(axis=1)
    if (prior.sum(axis=0) > party_targets).any():
        raise ValueError("Protected fixed seats exceed a party's seat target.")
    minimums, total, capacity = prepare_adjustment_bounds(
        base, v_desired_row_sums, kwargs)
    if int((party_targets - prior.sum(axis=0)).sum()) < total:
        raise ValueError("Party deficits are smaller than the adjustment-seat total.")

    initial, divisors = allocate_bounded_provisionally(
        votes, base + minimums, base + capacity, party_targets, prior,
        divisor_gen, total - int(minimums.sum()),
        rng=kwargs.get("rng"), on_tie=kwargs.get("on_tie"))
    allocation, switches = _switch_globally(
        votes, initial, party_targets, prior, divisors, minimums, capacity)

    added = allocation.sum(axis=1) - base
    if (int(added.sum()) != total or (added < minimums).any()
            or (added > capacity).any() or (allocation < prior).any()
            or (allocation.sum(axis=0) > party_targets).any()):
        raise RuntimeError(
            "Internal switching error: seat constraints violated.")

    steps = {
        "initial_allocation": [
            {"party": p, "goal": int(goal),
             "actual": int(initial[:, p].sum())}
            for p, goal in enumerate(party_targets)
        ],
        "switches": switches,
    }
    return allocation, {
        "data": steps,
        "function": print_initial_allocation,
        "functions": [print_initial_allocation, print_bounded_demo_table],
        "format": ("sccc", "clsls3"),
    }

def print_demo_table2(rules, steps):
    sup_header = "Switching of seats"
    headers = ["No.", "Constituency", "From", "To", "Min ratio"]
    data = []
    switch_number = 0
    for switch in steps["switches"]:
        switch_number += 1
        const_name = rules["constituencies"][switch["constituency"]]["name"]
        from_party = rules["parties"][switch["from"]]
        to_party   = rules["parties"][switch["to"]]
        ratio      = switch["ratio"]
        data.append([
            switch_number,
            const_name,
            from_party,
            to_party,
            ratio,
        ])

    return headers, data, sup_header 


def print_bounded_demo_table(rules, steps):
    sup_header = "Switching of seats"
    headers = [
        "No.", "From constituency", "From", "To constituency", "To",
        "Min ratio"]
    data = []
    for number, switch in enumerate(steps["switches"], start=1):
        data.append([
            number,
            rules["constituencies"][switch["from_constituency"]]["name"],
            rules["parties"][switch["from"]],
            rules["constituencies"][switch["to_constituency"]]["name"],
            rules["parties"][switch["to"]],
            switch["ratio"],
        ])
    return headers, data, sup_header
