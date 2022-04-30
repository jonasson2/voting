import heapq

from apportion import apportion1d
from table_util import v_subtract

def switching(m_votes,
              v_desired_row_sums,
              v_desired_col_sums,
              m_prior_allocations,
              divisor_gen,
              **kwargs):
    num_constituencies = len(v_desired_row_sums)
    num_parties        = len(v_desired_col_sums)
    assert num_constituencies == len(m_votes)
    assert num_constituencies == len(m_prior_allocations)
    assert all(num_parties == len(row) for row in m_votes)
    assert all(num_parties == len(row) for row in m_prior_allocations)

    v_prior_allocations = [sum(x) for x in zip(*m_prior_allocations)]
    # The number of adjustment seats each party should receive:
    correct_adj_seats = v_subtract(v_desired_col_sums, v_prior_allocations)

    # Allocate adjustment seats as if they were constituency seats
    m_adj_seats = []
    for c in range(len(m_prior_allocations)):
        votes = [m_votes[c][p] for p in range(len(m_votes[c]))]
#                 if correct_adj_seats[p] > 0 else 0
        alloc, div = apportion1d(
            v_votes=votes,
            num_total_seats=v_desired_row_sums[c],
            prior_allocations=m_prior_allocations[c],
            divisor_gen=divisor_gen
        )
        adj_seats = v_subtract(alloc, m_prior_allocations[c])
        m_adj_seats.append(adj_seats)

    v_adj_seats = [sum(x) for x in zip(*m_adj_seats)]
    initial_allocation = [{
        "party": p,
        "goal": v_desired_col_sums[p],
        "actual": v_prior_allocations[p] + v_adj_seats[p],
    } for p in range(num_parties)]

    # Transfer adjustment seats within constituencies from parties that have
    #  too many seats to parties that have too few seats, prioritized by
    #  "ratio", until all parties have the correct number of seats
    #  or no more swaps can be made:

    switches = []
    done = False
    while not done:
        v_adj_seats = [sum(x) for x in zip(*m_adj_seats)]
        diff_party = v_subtract(v_adj_seats, correct_adj_seats)

        over = [i for i in range(len(diff_party)) if diff_party[i] > 0]
        under = [i for i in range(len(diff_party)) if diff_party[i] < 0]
        ratio_heap = []
        for i in range(len(m_votes)):
            for j in over:
                for k in under:
                    if m_adj_seats[i][j] != 0 and m_votes[i][k] != 0:
                        gen_j = divisor_gen()
                        j_seats = m_prior_allocations[i][j]+m_adj_seats[i][j]
                        for x in range(j_seats):
                            div_j = next(gen_j)
                        gen_k = divisor_gen()
                        k_seats = m_prior_allocations[i][k]+m_adj_seats[i][k]
                        for x in range(k_seats+1):
                            div_k = next(gen_k)
                        r = (m_votes[i][j]/div_j) / (m_votes[i][k]/div_k)
                        heapq.heappush(ratio_heap, (r,(i,j,k)))

        done = len(ratio_heap) == 0
        if not done:
            # Find the constituency and pair of parties with the lowest
            # ratio, and transfer a seat:
            r, (i, j, k) = heapq.heappop(ratio_heap)
            m_adj_seats[i][j] -= 1
            m_adj_seats[i][k] += 1
            switches.append({
                "constituency": i,
                "from": j,
                "to": k,
                # "reason": "",
                "ratio": r,
            })

    steps = {
        "initial_allocation": initial_allocation,
        "switches": switches,
    }

    m_allocations = [[m_prior_allocations[c][p]+m_adj_seats[c][p]
                        for p in range(len(m_adj_seats[c]))]
                        for c in range(len(m_adj_seats))]

    return m_allocations, (steps, present_switching_sequence)



def present_switching_sequence(rules, steps):
    sup_headers = [{"text": "Nationally apportioned vs. full constituency allocation"
                    ,"colspan": 4},
                    {"text": "Switching of seats", "colspan": 5}]
    headers = [
        "Party", "Nationally apportioned", "All as const. seats", "Off by",
        "No.", "Constituency", "From", "To", "Ratio"]
    data = []
    for party in steps["initial_allocation"]:
        data.append([
            rules["parties"][party["party"]],
            party["goal"],
            party["actual"],
            party["actual"] - party["goal"],
            "",
            "",
            "",
            "",
            "",
        ])

    switch_number = 0
    for switch in steps["switches"]:
        switch_number += 1
        const_name = rules["constituencies"][switch["constituency"]]["name"]
        from_party = rules["parties"][switch["from"]]
        to_party   = rules["parties"][switch["to"]]
        ratio      = f'{switch["ratio"]:.3f}'
        if switch_number < len(steps["initial_allocation"]):
            data[switch_number-1][4] = switch_number
            data[switch_number-1][5] = const_name
            data[switch_number-1][6] = from_party
            data[switch_number-1][7] = to_party
            data[switch_number-1][8] = ratio
        else:
            data.append([
                "",
                "",
                "",
                "",
                switch_number,
                const_name,
                from_party,
                to_party,
                ratio,
            ])

    return headers, data, sup_headers
