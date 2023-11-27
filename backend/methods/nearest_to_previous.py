import numpy as np
def maxi(A, openC, openP):
    # Max of A and corresponding indices for non-full constituencies and parties
    amax = 0
    cmax = 0
    pmax = 0
    for c in openC:
        for p in openP:
            if A[c,p] >= amax:
                cmax = c
                pmax = p
                amax = A[c,p]
    return amax, cmax, pmax

def nearest_to_previous(m_votes,
                    v_desired_row_sums,
                    v_desired_col_sums,
                    m_prior_allocations,
                    divisor_gen,
                    last = None,
                    **kwargs):

    # CREATE NUMPY ARRAYS FROM PARAMETER LISTS
    votes = np.array(m_votes, float)
    alloc_list = np.array(m_prior_allocations)
    alloc_const = np.sum(alloc_list, 1)
    alloc_party = np.sum(alloc_list, 0)
    desired_const = np.array(v_desired_row_sums)
    desired_party = np.array(v_desired_col_sums)

    # LAST=VOTES/DIVISOR FOR LAST IN, LAST_QUOT=1 IN CONSTITUENCIES WITHOUT ALLOCATIONS
    if last is None:
        num_const = len(v_desired_row_sums)
        last_quot = np.zeros(num_const)
        last_index = np.full(num_const, None)
    else:
        last_quot = np.array([l["active_votes"] for l in last], float)
        last_index = np.array([l["idx"] for l in last])
    last_quot[alloc_const==0] = 1

    # CALCULATE DIVISORS
    N = max(max(desired_const), max(desired_party)) + 1
    div_gen = divisor_gen()
    divisors = np.array([next(div_gen) for i in range(N + 1)])

    # COUNT ALLOCATIONS
    num_allocated = sum([sum(x) for x in m_prior_allocations])
    num_total_seats = sum(v_desired_row_sums)
    
    # INITIALIZE SETS OF NON-FULL CONSTITUENCIES AND PARTIES, AND WORK MATRICES
    openC = set(k for (k,open) in enumerate(alloc_const < desired_const) if open)
    openP = set(k for (k,open) in enumerate(alloc_party < desired_party) if open)
    next_quot = np.zeros(alloc_list.shape)
    ratio = np.zeros(alloc_list.shape)
    for c in openC:
        for p in openP:
            next_quot[c,p] = votes[c,p]/divisors[alloc_list[c,p]]
            print(f"c,p={c},{p}, {next_quot[c,p]=}, {last_quot[c]=}")
            ratio[c,p] = next_quot[c,p]/last_quot[c]

    # PRIMARY LOOP: REPEATEDLY ALLOCATE SEAT WITH MAXIMUM RATIO OF NEXT TO LAST
    allocation_sequence = []
    while num_allocated < num_total_seats:
        (max_ratio, maxC, maxP) = maxi(ratio, openC, openP)
        alloc_list[maxC, maxP] += 1
        alloc_const[maxC] += 1
        alloc_party[maxP] += 1
        num_allocated += 1
        if num_allocated == num_total_seats:
            break

        # REMOVE CONST AND/OR PARTY WHEN FULL
        if alloc_party[maxP] == desired_party[maxP]:
            openP.remove(maxP)
        if alloc_const[maxC] == desired_const[maxC]:
            openC.remove(maxC)
        else: # There is no "last_quot" for parties, that explaines this funny if-else
            # UPDATE WORK MATRICES IN CONSTITUENCY WITH MAX RATIO
            last_quot[maxC] = next_quot[maxC, maxP]
            next_quot[maxC, maxP] = (votes[maxC, maxP] /
                                     divisors[alloc_list[maxC, maxP]])
            for p in openP:
                print(f"maxC,p={maxC},{p}, {next_quot[maxC,p]=}, {last_quot[maxC]=}")
                if last_quot[maxC] > 0:
                    ratio[maxC, p] = next_quot[maxC, p]/last_quot[maxC]
                else:
                    ratio[maxC, p] = 0

        # DATA FOR STEP-BY-STEP TABLE
        reason = "VOTE" if alloc_const[maxC] == 1 else "MAX"
        allocation = {"constituency": maxC, "last":last_index[maxC],
                      "ratio": max_ratio, "party": maxP, "reason": reason}
        last_index[maxC] = maxP
        allocation_sequence.append(allocation)
    stepbystep = {"data": allocation_sequence, "function": print_demo_table}
    return alloc_list, stepbystep

def print_demo_table(rules, allocation_sequence):
    # CONSTRUCT STEP-BY-STEP TABLE
    headers = ["Adj. seat #", "Constituency", "Next party", "Last party",
               "Criteria", "Score/ratio of scores"]
    criterion = {}
    criterion["MAX"] = "Max ratio of next-in to previous-in vote score"
    criterion["VOTE"] = "No const. seat, thus using max list vote"
    data = []
    for (seat_number, allocation) in enumerate(allocation_sequence):
        reason = allocation["reason"]
        last_index = allocation["last"]
        last_party = rules["parties"][last_index] if last_index!=None else "–"
        data.append([
            seat_number + 1,
            rules["constituencies"][allocation["constituency"]]["name"],            
            rules["parties"][allocation["party"]],
            last_party,
            criterion[reason],
            allocation["ratio"] if reason == "MAX" else round(allocation["ratio"])
        ])

    return headers, data, None
