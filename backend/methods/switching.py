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
        alloc_const, _,_,_ = apportion1d_general(
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
    while True:
        i += 1
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
                C.append(c)
                P.append(p)
                Q.append(q)
                ratio.append(min_score/max_score)

        # FIND THE SMALLEST RATIO AND SWITCH WITHIN THE CORRESPONDING CONSTITUENCY
        if not C:
            print('No surplus/wanting pair found')
            print('  surplus:', find(surplus))
            print('  wanting:', find(wanting))
            break
        else:
            cmin = np.argmin(ratio)
            alloc[C[cmin], P[cmin]] -= 1
            alloc[C[cmin], Q[cmin]] += 1
            # print(f'- switching parties {P[cmin]} and {Q[cmin]} in const. {C[cmin]})')
            switches.append({
                "constituency": C[cmin],
                "from": P[cmin],
                "to": Q[cmin],
                "ratio": ratio[cmin]
                })

    # INFORMATION FOR SECOND STEP-BY-STEP DEMO TABLE
    steps = {
        "initial_allocation": initial_allocation,
        "switches": switches,
    }

    return alloc.tolist(), (steps, print_demo_table1, print_demo_table2) 

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
