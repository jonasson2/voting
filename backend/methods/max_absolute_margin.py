import numpy as np

def maxi(A, openC, openP):
    amax = 0
    for c in openC:
        p1 = min(openP)
        for p in openP:
            if A[c,p] > A[c,p1]:
                p1 = p
        p2 = None
        for p in openP:
            if p != p1:
                if p2 is None or A[c,p] > A[c,p2]:
                    p2 = p
        
        difference = (A[c,p1] - A[c,p2]) if p2 is not None and A[c,p2] != 0 else 0
        if difference >= amax:
            cmax = c
            pmax = p1
            pnext = p2 if p2 is not None and A[c,p2] != 0 else None
            amax = difference
    return amax, cmax, pmax, pnext

def max_absolute_margin(m_votes,
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
    openC = set(k for (k,open) in enumerate(alloc_const < desired_const) if open)
    openP = set(k for (k,open) in enumerate(alloc_party < desired_party) if open)
    next_quot = np.zeros(alloc_list.shape)
    for c in openC:
        for p in openP:
            next_quot[c,p] = votes[c,p]/divisors[alloc_list[c,p]]

    # PRIMARY LOOP: REPEATEDLY ALLOCATE SEAT WITH MAXIMUM DIFFERENCE OF NEXT TO SECOND NEXT
    allocation_sequence = []
    while num_allocated < num_total_seats:
        (max_diff, maxC, maxP, nextP) = maxi(next_quot, openC, openP)
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
            next_quot[maxC, maxP] = (votes[maxC, maxP] /
                                     divisors[alloc_list[maxC, maxP]])

        # DATA FOR STEP-BY-STEP TABLE
        reason = "MAX" if max_diff != 0 else "LAST"
        allocation = {"constituency": maxC, "party": maxP, "nextParty": nextP,
                      "difference": max_diff, "reason": reason}
        allocation_sequence.append(allocation)
    stepbystep = {"data": allocation_sequence, "function": print_demo_table}
    return alloc_list.tolist(), stepbystep

def print_demo_table(rules, allocation_sequence):
    # CONSTRUCT STEP-BY-STEP TABLE
    headers = ["Adj. seat #", "Constituency", "Next party", "Second next party",
               "Criteria", "Score difference"]
    criterion = {}
    criterion["MAX"] = "Max next-in and next-but-one-in vote score difference"
    criterion["LAST"] = "Last list"
    data = []
    for (seat_number, allocation) in enumerate(allocation_sequence):
        reason = allocation["reason"]
        next_index = allocation["nextParty"]
        next_party = rules["parties"][next_index] if next_index != None else "–"
        data.append([
            seat_number + 1,
            rules["constituencies"][allocation["constituency"]]["name"],            
            rules["parties"][allocation["party"]],
            next_party,
            criterion[reason],
            allocation["diff"] if allocation["diff"] != 0 else "N/A"
        ])

    return headers, data, None
