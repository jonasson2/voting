#coding:utf-8
from copy import deepcopy, copy
from apportion import apportion1d, superiority, compute_forced, forced_stepbystep_entries
import numpy as np
from numpy import flatnonzero as find
    
def specified_col_sums_allocate(votes, total_const_seats, total_party_seats,
                                prior_alloc, div_gen, compute_criteria,
                                criterion_name, reason):

    # PREPARE WORK ARRAYS
    nconst = len(total_const_seats)
    alloc_list = prior_alloc.copy()
    free_const_seats = total_const_seats - alloc_list.sum(1)
    free_party_seats = total_party_seats - alloc_list.sum(0)
    criteria = -np.ones(nconst)
    party = np.zeros(nconst, int)

    # CALCULATE DIVISORS
    N = max(max(total_const_seats), max(total_party_seats)) + 1
    gen = div_gen()
    div = np.array([next(gen) for _ in range(N + 1)])

    # ALLOCATE SEATS ONE BY ONE
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
        openC = free_const_seats > 0
        openP = free_party_seats > 0
        if sum(openP) == 1:
            print(sum(openP))
            pass

        # DETERMINE CRITERION FOR EACH NON-FULL CONSTITUENCY
        for c in find(openC):
            (party[c], criteria[c]) = compute_criteria(
                votes[c,openP], alloc_list[c,openP], div, nseats=total_const_seats[c],
                npartyseats=total_party_seats, criterion=criteria[c])

        # SELECT CONSTITUENCY AND PARTY WITH MAXIMUM CRITERION
        maxC = np.argmax(criteria)
        maxP = party[maxC]
        alloc_list[maxC, maxP] += 1
        allocation_sequence.append({
            "const": maxC,
            "party": maxP,
            "reason": reason,
            "maximum": criteria.max()
        })
        free_const_seats[maxC] -= 1
        free_party_seats[maxP] -= 1
        if free_const_seats[maxC] <= 0:
            criteria[maxC] = -1
        if not all(free_const_seats >= 0):
            print(free_const_seats)
            #assert all(free_const_seats >= 0)

    # PREPARE OBJECTS TO RETURN
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
