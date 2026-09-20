import numpy as np
from methods.provisional_allocation import allocate_provisionally
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

def switching(m_votes,
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
    div_gen = divisor_gen()
    divisors = np.array([next(div_gen) for i in range(N + 1)])
    if (not np.isfinite(divisors).all() or (divisors <= 0).any()
            or (np.diff(divisors) < 0).any()):
        raise ValueError("Switching requires positive, finite, nondecreasing divisors.")
    
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
