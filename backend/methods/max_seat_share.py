#coding:utf-8
from copy import deepcopy
import numpy as np
from numpy import flatnonzero as find
from apportion import compute_forced, forced_stepbystep_entries

def super_explain(c, p, super):
    return {'constituency': c, 'party': p, 'superiority': super, 'reason': super_reason}

def max_const_seat_share(
        m_votes,
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
    const_seats = total_const_seats - alloc_list.sum(1)
    party_seats = total_party_seats - alloc_list.sum(0)

    # CALCULATE DIVISORS
    N = max(max(total_const_seats), max(total_party_seats)) + 1
    div_gen = divisor_gen()
    div = np.array([next(div_gen) for _ in range(N + 1)])

    allocation_sequence = []
    while any(const_seats):
        # FORCED ALLOCATION
        forced = compute_forced(votes, const_seats, party_seats)
        alloc_list += forced
        const_seats -= forced.sum(1)
        party_seats -= forced.sum(0)

        # Eftirfarandi þarf auðvitað ekki í simúleringu...
        allocation_sequence.extend(forced_stepbystep_entries(forced))
        if not any(const_seats):
            break

        # ALLOCATE WITH MAXIMUM RELATIVE SUPERIORITY
        openC = find(const_seats > 0)
        openP = find(party_seats > 0)
        assert len(openP) != 1
        for c in openC:
            (p,s) = superiority(votes[c,openP], alloc_list[c,openP], const_seats[c],
                                party_seats,
                                div, div_gen)
            party.append(p)
            super.append(s)
        imax = np.argmax(super)
        maxC = openC[np.argmax(super)]
        maxP = openP[party[imax]]
        alloc_list[maxC, maxP] += 1
        allocation_sequence.append(super_explain(maxC, maxP, super[imax]))
        const_seats[maxC] -= 1
        party_seats[maxP] -= 1
    stepbystep = {"data": allocation_sequence, "function": print_demo_table}
    return alloc_list.tolist(), stepbystep

    m_allocations = deepcopy(m_prior_allocations)

    num_allocated = sum([sum(c) for c in m_allocations])
    total_seats = sum(v_desired_row_sums)
    allocation_sequence = []

    for n in range(total_seats - num_allocated):
        m_seat_props = []
        maximums = []
        for c in range(len(m_votes)):
            m_seat_props.append([])
            s = sum(m_votes[c])
            for p in range(len(m_votes[c])):
                col_sum = sum(row[p] for row in m_allocations)
                if col_sum < v_desired_col_sums[p]:
                    div = divisor_gen()
                    for k in range(m_allocations[c][p]+1):
                        divisor = next(div)
                    seat_share = (float(m_votes[c][p])/s)*v_desired_row_sums[c]/divisor
                else:
                    seat_share = 0
                m_seat_props[c].append(seat_share)
            maximums.append(max(m_seat_props[c]))

            if sum(m_allocations[c]) == v_desired_row_sums[c]:
                m_seat_props[c] = [0]*len(m_votes[c])
                maximums[c] = 0

        maximum = max(maximums)
        const = maximums.index(maximum)
        party = m_seat_props[const].index(maximum)

        m_allocations[const][party] += 1
        allocation_sequence.append({
            "constituency": const, "party": party,
            "reason": "Max over all lists",
            "maximum": maximum,
        })

    stepbystep = {"data": allocation_sequence, "function": print_demo_table}
    return m_allocations, stepbystep

def print_demo_table(rules, allocation_sequence):
    headers = ["Adj. seat #", "Constituency", "Party",
        "Criteria", "Const. seat share score"]
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
