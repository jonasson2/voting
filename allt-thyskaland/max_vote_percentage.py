#coding:utf-8
import numpy as np
from numpy import ix_

def max_vote_percentage(
       m_votes,
       v_desired_row_sums,
       v_desired_col_sums,
       m_prior_allocations,
       divisor_gen,
       **kwargs):

    # CREATE NUMPY ARRAYS FROM PARAMETER LISTS
    votes = np.array(m_votes, float)
    alloc_list = np.array(m_prior_allocations)
    alloc_const = np.sum(alloc_list, 1)
    alloc_party = np.sum(alloc_list, 0)
    desired_const = np.array(v_desired_row_sums)
    desired_party = np.array(v_desired_col_sums)

    # CALCULATE DIVISORS
    N = max(max(desired_const), max(desired_party)) + 1
    div_gen = divisor_gen()
    divisors = np.array([next(div_gen) for i in range(N + 1)])

    # COUNT ALLOCATIONS
    num_allocated = sum([sum(x) for x in m_prior_allocations])
    num_total_seats = sum(v_desired_row_sums)

    # INITIALIZE SETS OF NON-FULL CONSTITUENCIES AND PARTIES, AND QUOTIENT MATRIX
    openC = [k for (k,open) in enumerate(alloc_const < desired_const) if open]
    openP = [k for (k,open) in enumerate(alloc_party < desired_party) if open]
    quot = np.zeros(alloc_list.shape)
    for c in openC:
        for p in openP:
            quot[c,p] = votes[c,p]/divisors[alloc_list[c,p]]

    # PRIMARY LOOP: REPEATEDLY ALLOCATE SEAT WITH MAXIMUM VOTE PERCENTAGE QUOTIENT
    allocation_sequence = []
    const_votes = votes.sum(axis=1)
    quot_share = quot/const_votes[:, None]
    while num_allocated < num_total_seats:
        A = quot_share[ix_(openC, openP)]
        column_maxima = A.max(0)
        j = column_maxima.argmax()
        i = A[:,j].argmax()
        (maxC, maxP) = (openC[i], openP[j])
        alloc_list[maxC, maxP] += 1
        alloc_const[maxC] += 1
        alloc_party[maxP] += 1
        num_allocated += 1

        # REMOVE CONST AND/OR PARTY WHEN FULL; UPDATE QUOTIENTS
        if alloc_party[maxP] == desired_party[maxP]:
            openP.remove(maxP)
        if alloc_const[maxC] == desired_const[maxC]:
            openC.remove(maxC)
        else:
            divisor = divisors[alloc_list[maxC, maxP]]
            quot_share[maxC, maxP] = votes[maxC, maxP]/const_votes[maxC]/divisor

        # APPEND TO STEP-BY-STEP TABLE
        allocation_sequence.append({
            "constituency": maxC, "party": maxP,
            "reason": "Max over all lists",
            "maximum": quot_share[maxC, maxP],
        })

    return alloc_list.tolist(), (allocation_sequence, print_demo_table)

def print_demo_table(rules, allocation_sequence):
    headers = ["Adj. seat #", "Constituency", "Party",
        "Criteria", "Const. vote score percentage"]
    data = []
    seat_number = 0

    for allocation in allocation_sequence:
        seat_number += 1
        data.append([
            seat_number,
            rules["constituencies"][allocation["constituency"]]["name"],
            rules["parties"][allocation["party"]],
            allocation["reason"],
            allocation["maximum"]
        ])

    return headers, data, None
