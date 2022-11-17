#coding:utf-8
from copy import deepcopy, copy
from apportion import apportion1d, superiority, compute_forced, forced_stepbystep_entries
import numpy as np
from numpy import flatnonzero as find

super_reason="Max ratio over constit. of next-in vote score to first substitute vote score"

def super_explain(c, p, super):
    return {'const': c, 'party': p, 'superiority': super, 'reason': super_reason}

def superiority(votes, alloc, nseats, div, npartyseats):
    score = votes/div[alloc]
    seats = alloc.copy()
    party_next = np.argmax(score)
    score_next = score[party_next]
    score[party_next] = 0  # þessi lína eða sú næsta ekki báðar
    # seats[party_next] += 1
    nalloc = 1
    while True:
        if all(score == 0):
            return party_next, 10000000
        party = np.argmax(score)
        seats[party] += 1
        score[party] = votes[party]/div[seats[party]]
        nalloc += 1
        if nalloc > nseats:
            super = score_next/score[party]
            return party_next, super
        if seats[party] >= npartyseats[party]:
           score[party] = 0

def rel_sup(m_votes,
            v_desired_row_sums,
            v_desired_col_sums,
            m_prior_allocations,
            divisor_gen,
            **kwargs):

    # CREATE NUMPY ARRAYS FROM PARAMETER LISTS
    votes = np.array(m_votes, float)
    alloc_list = np.array(m_prior_allocations)
    total_party_seats = np.array(v_desired_col_sums)
    total_const_seats = np.array(v_desired_row_sums)
    free_const_seats = total_const_seats - alloc_list.sum(1)
    free_party_seats = total_party_seats - alloc_list.sum(0)

    # CALCULATE DIVISORS
    N = max(max(total_const_seats), max(total_party_seats)) + 1
    div_gen = divisor_gen()
    div = np.array([next(div_gen) for _ in range(N + 1)])

    allocation_sequence = []
    while any(free_const_seats):
        # FORCED ALLOCATION
        forced = compute_forced(votes, free_const_seats, free_party_seats)
        alloc_list += forced
        free_const_seats -= forced.sum(1)
        free_party_seats -= forced.sum(0)
        allocation_sequence.extend(forced_stepbystep_entries(forced))
        if not any(free_const_seats):
            break

        # ALLOCATE WITH MAXIMUM RELATIVE SUPERIORITY
        super = []
        party = []
        openC = find(free_const_seats > 0)
        openP = find(free_party_seats > 0)
        assert len(openP) != 1

        for c in openC:
            (p,s) = superiority(votes[c,openP], alloc_list[c,openP],
                                free_const_seats[c], div, total_party_seats)
            party.append(p)
            super.append(s)
        imax = np.argmax(super)
        maxC = openC[np.argmax(super)]
        maxP = openP[party[imax]]
        alloc_list[maxC, maxP] += 1
        allocation_sequence.append(super_explain(maxC, maxP, super[imax]))
        free_const_seats[maxC] -= 1
        free_party_seats[maxP] -= 1
    stepbystep = {"data": allocation_sequence, "function": print_demo_table}
    return alloc_list.tolist(), stepbystep

def print_demo_table(rules, allocation_sequence):
    headers = ["Adj. seat #", "Constituency", "Party",
        "Criteria", "Superiority ratio"]
    data = []
    seat_number = 0

    for allocation in allocation_sequence:
        seat_number += 1
        superiority = allocation["superiority"] if "superiority" in allocation else "N/A"
        data.append([
            seat_number,
            rules["constituencies"][allocation["const"]]["name"],
            rules["parties"][allocation["party"]],
            allocation["reason"],
            superiority,
        ])
    print(data)
    return headers, data, None
