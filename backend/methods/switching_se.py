from apportion import apportion1d_general
import numpy as np
from numpy import argmin, flatnonzero as find
from copy import deepcopy

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
    votes = np.array(m_votes, float)
    alloc_prior = np.array(m_prior_allocations)
    desired_const = np.array(v_desired_row_sums)
    max_party = np.array(v_desired_col_sums)
    num_constituencies = len(v_desired_row_sums)
    num_parties        = len(v_desired_col_sums)
    assert(sum(max_party) >= sum(desired_const))

    # CALCULATE DIVISORS
    N = max(max(desired_const), max(max_party)) + 1
    div_gen = divisor_gen()
    divisors = np.array([next(div_gen) for i in range(N + 1)])
    
    # ALLOCATE ADJUSTMENT SEATS AS IF THEY WERE FIXED SEATS
    alloc= np.zeros((num_constituencies, num_parties), int)
    temp_votes = deepcopy(votes)
    full = [p for p in range(num_parties) if sum(alloc_prior[:,p]) >= max_party[p]]
    temp_votes[:,full] = 0
    for c in range(num_constituencies):
        alloc_const, _,_ = apportion1d_general(
            v_votes = list(temp_votes[c,:]),
            num_total_seats = desired_const[c],
            prior_allocations = list(alloc_prior[c,:]),
            rule = divisor_gen
        )
        alloc[c,:] = np.array(alloc_const)

    # INFORMATION FOR FIRST STEP-BY-STEP DEMO TABLE
    initial_allocation = [{
        "party": p,
        "goal": int(max_party[p]),
        "actual": int(sum(alloc[:,p]))
    } for p in range(num_parties)]

    # WHILE SOME PARTIES HAVE TOO MANY SEATS DO SWITCHING
    switches = []
    i = 0
    votesum = [sum(votes[c]) for c in range(num_constituencies)]
    seatshares = np.array([
        [votes[c, p]/votesum[c]*desired_const[c] for p in range(num_parties)]
        for c in range(num_constituencies)
    ])
    while True:
        i += 1
        surplus = sum(alloc,0) > max_party
        if not any(surplus):
            break
        wanting = sum(alloc,0) < max_party

        # CALCULATE MINIMUM SEAT SHARE OF SURPLUS PARTIES
        P = []
        Q = []
        C = []
        mincrit = []
        for c in range(num_constituencies):
            with_seats = alloc[c,:] > alloc_prior[c,:]
            with_votes = votes[c,:] > 0
            score = np.zeros(num_parties)
            S = surplus & with_seats
            score[S] = seatshares[c, S]/divisors[alloc[c, S] - 1]
            if any(S):
                (min_score, p) = min_with_index(score, S)
                C.append(c)
                P.append(p)
                mincrit.append(min_score)
        if not C:  # NO SURPLUS PARTIES LEFT
            break
        else:
            cmin = np.argmin(mincrit)
            c = C[cmin]
            with_votes = votes[c,:] > 0
            scoreto = np.zeros(num_parties)
            W = wanting & with_votes
            scoreto[W] = seatshares[c, W]/divisors[alloc[c, W]]
            if not any(W):
                break
            else:
                (maxcrit, q) = max_with_index(scoreto, W)
                alloc[c, P[cmin]] -= 1
                alloc[c, q] += 1

                switches.append({
                    "constituency": c,
                    "from": P[cmin],
                    "to": q,
                    "mincrit": mincrit[cmin],
                    "maxcrit": maxcrit
                })

    # INFORMATION FOR SECOND STEP-BY-STEP DEMO TABLE
    steps = {
        "initial_allocation": initial_allocation,
        "switches": switches,
    }

    stepbystep = {
        "data": steps,
        "function": print_demo_table1,
        "additional_function": print_demo_table2
    }
    return alloc, stepbystep

def print_demo_table1(rules, steps):
    sup_header = "Nationally apportioned vs. full constituency allocation"
    headers = ["Party", "Nationally apportioned", "All as const. seats", "Off by"]
    data = []
    for party in steps["initial_allocation"]:
        data.append([
            rules["parties"][party["party"]],
            party["goal"],
            party["actual"],
            party["actual"] - party["goal"],
        ])
    return headers, data, sup_header 

def print_demo_table2(rules, steps):
    sup_header = "Switching of seats"
    headers = ["No.", "Constituency", "From", "To", "Min crit", "Max crit"]
    data = []
    switch_number = 0
    for switch in steps["switches"]:
        switch_number += 1
        const_name = rules["constituencies"][switch["constituency"]]["name"]
        from_party = rules["parties"][switch["from"]]
        to_party   = rules["parties"][switch["to"]]
        mincrit    = switch["mincrit"]
        maxcrit    = switch["maxcrit"]
        data.append([
            switch_number,
            const_name,
            from_party,
            to_party,
            mincrit,
            maxcrit
        ])

    return headers, data, sup_header 
