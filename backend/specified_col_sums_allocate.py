#coding:utf-8
from copy import deepcopy, copy
from apportion import apportion1d, superiority, compute_forced, forced_stepbystep_entries
import numpy as np
from numpy import flatnonzero as find

super_reason="Max ratio of next-in vote score to computed substitute vote score"

def compute_superiority(votes, alloc, nseats, div, npartyseats):
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
    alloc, stepbystep = specified_col_sums_allocate(
        m_votes,
        v_desired_row_sums,
        v_desired_col_sums,
        m_prior_allocations,
        divisor_gen,
        compute_superiority,
        "Superiority ratio",
        super_reason
    )
    return alloc, stepbystep
    
def specified_col_sums_allocate(votes, row_sums, col_sums, prior_alloc, div_gen,
                                compute_criteria, criterion_name, reason):

    # CREATE NUMPY ARRAYS FROM PARAMETER LISTS
    votes = np.array(votes, float)
    alloc_list = np.array(prior_alloc)
    total_party_seats = np.array(col_sums)
    total_const_seats = np.array(row_sums)
    free_const_seats = total_const_seats - alloc_list.sum(1)
    free_party_seats = total_party_seats - alloc_list.sum(0)

    # CALCULATE DIVISORS
    N = max(max(total_const_seats), max(total_party_seats)) + 1
    gen = div_gen()
    div = np.array([next(gen) for _ in range(N + 1)])

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

        # PREPARE NOT-FORCED ALLOCATION
        criteria_list = []
        party = []
        openC = find(free_const_seats > 0)
        openP = find(free_party_seats > 0)
        assert len(openP) != 1

        # LOOP OVER NON-FILLED CONSTITUENCIES
        for c in openC:
            (p,c) = compute_criteria(votes[c,openP], alloc_list[c,openP],
                                     free_const_seats[c], div, total_party_seats)
            party.append(p)
            criteria_list.append(c)
        imax = np.argmax(criteria_list)
        maxC = openC[np.argmax(criteria_list)]
        maxP = openP[party[imax]]
        alloc_list[maxC, maxP] += 1
        allocation_sequence.append({
            "const": maxC,
            "party": maxP,
            "reason": reason,
            "maximum": criteria_list[imax]
        })
        free_const_seats[maxC] -= 1
        free_party_seats[maxP] -= 1
    data = {"name":criterion_name, "sequence": allocation_sequence}
    stepbystep = {"data": data, "function": print_demo_table}
    return alloc_list.tolist(), stepbystep

def print_demo_table(rules, data):
    alloc_seq = data["sequence"]
    criterion_name = data["name"]
    headers = [
        "Adj. seat #",
        "Constituency",
        "Party",
        "Criteria",
        criterion_name]
    seat_number = 0
    contents = []
    for alloc in alloc_seq:
        seat_number += 1
        maximum = alloc["maximum"] if "maximum" in alloc else "np.nan"
        contents.append([
            seat_number,
            rules["constituencies"][alloc["const"]]["name"],
            rules["parties"][alloc["party"]],
            alloc["reason"],
            maximum,
        ])

    return headers, contents, None
