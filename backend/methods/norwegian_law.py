#coding:utf-8
from copy import deepcopy

def norwegian_apportionment(m_votes,
                            v_desired_row_sums,
                            v_desired_col_sums,
                            m_prior_allocations,
                            divisor_gen,
                            v_fixed_seats,
                            **kwargs):
    m_allocations = deepcopy(m_prior_allocations)

    num_allocated = sum([sum(c) for c in m_allocations])
    total_seats = sum(v_desired_row_sums)
    allocation_sequence = []

    for n in range(total_seats-num_allocated):
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
                    seat_factor = max(1, v_fixed_seats[c])
                    a = float(m_votes[c][p])*seat_factor/s/divisor
                else:
                    a = 0
                m_seat_props[c].append(a)
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
        "Criteria", "Special const. seat share score"]
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
