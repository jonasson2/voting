#coding:utf-8
from copy import deepcopy, copy
from apportion import apportion1d, threshold_elimination_constituencies

def nearest_neighbor(m_votes,
                     v_desired_row_sums,
                     v_desired_col_sums,
                     m_prior_allocations,
                     divisor_gen,
                     **kwargs):

    assert("last" in kwargs)
    last = kwargs["last"]

    m_allocations = deepcopy(m_prior_allocations)
    num_allocated = sum([sum(x) for x in m_allocations])
    num_total_seats = sum(v_desired_row_sums)
    allocation_sequence = []
    for n in range(num_total_seats-num_allocated):
        m_votes = threshold_elimination_constituencies(m_votes, 0.0,
                    v_desired_col_sums, m_allocations)
        neighbor_ratio = []
        first_in = []
        next_used = []
        reason = []
        eps = 0.1
        for c in range(len(m_votes)):
            seats_left = v_desired_row_sums[c] - sum(m_allocations[c])
            if not seats_left:
                neighbor_ratio.append(1e8)
                reason.append("Ratio set to 100000000")
                first_in.append(0)
                next_used.append(0)
                continue

            # Find the party next in line in the constituency:
            next_alloc_num = sum(m_allocations[c]) + 1
            alloc_next, div = apportion1d(m_votes[c], next_alloc_num,
                                   m_allocations[c], divisor_gen)
            # Með upphaflegum atkvæðum m_votes=[[1000,0],[1001,999]],
            # num_total_seats=3, num_allocated=0, v_desired_col_sums=[2,1],
            # v_desired_row_sums=[2,1] fæst hér, þegar n=2 og c=0, m_votes=
            # [[0,0],[0,999]], next_alloc_num=2, m_allocations=[[1,0],[1,0]]
            # og í kjölfarið tekst ekki að úthluta með apportion1d
            diff = [alloc_next[p]-m_allocations[c][p]
                    for p in range(len(m_votes[c]))]
            next_in = diff.index(1)
            first_in.append(next_in)
            next_used.append(div[2])

            # Calculate neighbor ratio:
            if last[c] == 0:
                nr = eps/next_used[c]
                reason.append("Order of max list vote, as there is no "
                              "previous allocation")
            elif next_used[c] > 0:
                reason.append("Min ratio of last to next quotient of list vote")
                nr = float(last[c])/next_used[c]
            else:
                nr = 1e8
                reason.append["Ratio set to 100000000"]
            neighbor_ratio.append(nr)

        # Allocate seat in constituency where the calculated
        #  neighbor ratio is lowest:
        least = min(neighbor_ratio)
        idx = neighbor_ratio.index(least)
        m_allocations[idx][first_in[idx]] += 1
        allocation_sequence.append({
            "constituency": idx, "party": first_in[idx],
            "reason": reason[idx],
            "min": least,
        })
    pass
    return m_allocations, (allocation_sequence, present_allocation_sequence)


def present_allocation_sequence(rules, allocation_sequence):
    headers = ["Adj. seat #", "Constituency", "Party",
        "Criteria", "Neighbor ratio"]
    data = []
    seat_number = 0

    for allocation in allocation_sequence:
        seat_number += 1
        data.append([
            seat_number,
            rules["constituencies"][allocation["constituency"]]["name"],
            rules["parties"][allocation["party"]],
            allocation["reason"],
            round(allocation["min"], 3),
        ])

    return headers, data
