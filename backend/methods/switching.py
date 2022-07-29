from apportion import apportion1d_general
import numpy as np

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
    for c in range(num_constituencies):
        alloc_const, _,_,_ = apportion1d_general(
            v_votes = list(votes[c,:]),
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
    while True:
        last_surplus = -np.ones(num_constituencies, int)
        first_wanting = -np.ones(num_constituencies, int)
        ratio = np.ones(num_constituencies)*np.inf
        surplus = set(p for p in range(num_parties) if sum(alloc[:,p]) > max_party[p])
        if not surplus:
            break
        wanting = set(p for p in range(num_parties) if sum(alloc[:,p]) < max_party[p])

        # CALCULATE MINIMUM RATIO OF ACTIVE VOTES IN EACH CONSTITUENCY
        for c in range(num_constituencies):
            quot_min = np.inf
            for p in range(num_parties):
                quot = votes[c,p]/divisors[alloc[c,p] - 1]
                if p in surplus and alloc[c,p] > alloc_prior[c,p] and quot <= quot_min:
                    quot_min = quot
                    last_surplus[c] = p
            quot_max = 0
            for p in range(num_parties):
                quot = votes[c,p]/divisors[alloc[c,p]]
                if p in wanting and quot >= quot_max:
                    quot_max = quot
                    first_wanting[c] = p
            if last_surplus[c] >= 0 and first_wanting[c] >= 0:
                ratio[c] = quot_min/quot_max

        # FIND THE SMALLEST RATIO AND SWITCH WITHIN THE CORRESPONDING CONSTITUENCY
        cmin = np.argmin(ratio)
        assert(not np.isinf(cmin))

        alloc[cmin, last_surplus[cmin]] -= 1
        alloc[cmin, first_wanting[cmin]] += 1
        switches.append({
            "constituency": cmin,
            "from": last_surplus[cmin],
            "to": first_wanting[cmin],
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
