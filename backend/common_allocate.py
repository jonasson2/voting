#coding:utf-8
from copy import deepcopy, copy
from apportion import superiority, compute_forced, forced_stepbystep_entries
import numpy as np
from numpy import flatnonzero as find

def common_allocate(
        votes, total_const_seats, total_party_seats, prior_alloc, div_gen,
        compute_criteria, criterion_name, reason, nolast_reason=None, last=None, **kwargs):

    # PREPARE WORK ARRAYS
    nconst = len(total_const_seats)
    alloc_list = prior_alloc.copy()
    free_const_seats = total_const_seats - alloc_list.sum(1)
    free_party_seats = total_party_seats - alloc_list.sum(0)
    party = -np.ones(nconst, int)
    has_last = last is not None

    # CALCULATE DIVISORS
    N = max(max(total_const_seats), max(total_party_seats)) + 1
    gen = div_gen()
    div = np.array([next(gen) for _ in range(N + 1)])

    # ALLOCATE SEATS ONE BY ONE
    allocation_sequence = []
    last_party = [l['idx'] for l in last] if has_last else np.full(nconst, None)

    votesum = votes.sum(1)
    while any(free_const_seats):
        # FORCED ALLOCATION
        forced, forced_party = compute_forced(votes, free_const_seats, free_party_seats)
        alloc_list += forced
        free_const_seats -= forced.sum(1)
        free_party_seats -= forced.sum(0)
        allocation_sequence.extend(forced_stepbystep_entries(forced, has_last))
        last_party = np.where(forced_party >=0, forced_party, last_party)
        if not any(free_const_seats):
           break

        # PREPARE NOT-FORCED ALLOCATION
        openC = find(free_const_seats > 0)
        openP = find(free_party_seats > 0)

        # DETERMINE CRITERION FOR EACH NON-FULL CONSTITUENCY
        criteria = np.zeros(len(openC))
        last_score = np.zeros(len(openC))
        for (k,c) in enumerate(openC):
            lp = find(openP==last_party[c])[0] if last_party[c] in openP else None
            (p, criteria[k]) = compute_criteria(
                votes[c,openP],
                alloc_list[c,openP],
                div,
                votesum = votesum[c],
                nfree = free_const_seats[c],
                totconstseats = total_const_seats[c],
                npartyseats = total_party_seats[openP],
                last_party = lp,
                )
            party[c] = openP[p]

        # SELECT CONSTITUENCY AND PARTY WITH MAXIMUM CRITERION
        maxC = openC[np.argmax(criteria)]
        maxP = party[maxC]
        last_party[maxC] = maxP
        alloc_list[maxC, maxP] += 1

        allocation_sequence.append({
            "const": maxC,
            "last_party": last_party[c] if has_last else None,
            "party": maxP,
            "reason": nolast_reason if has_last and last_party[c] is None else reason,
            "maximum": criteria.max()
        })
        free_const_seats[maxC] -= 1
        free_party_seats[maxP] -= 1
        #print(free_const_seats) #Todo
        #print(free_party_seats)
        assert all(free_const_seats >= 0)
        assert all(free_party_seats >= 0)

    # PREPARE OBJECTS TO RETURN
    data = {"name":criterion_name, "sequence": allocation_sequence}
    stepbystep = {"data": data, "function": print_demo_table}
    return alloc_list, stepbystep

def print_demo_table(rules, data):
    alloc_seq = data["sequence"]
    criterion_name = data["name"]
    has_last = (alloc_seq and "last_party" in alloc_seq[0]
                and alloc_seq[0]["last_party"] is not None)
    headers = [
        "Adj. seat #",
        "Constituency",
        "Next party" if has_last else "Party",
        "Criteria",
        criterion_name]
    if has_last:
        headers.insert(3, "Last party")
    seat_number = 0
    contents = []
    for alloc in alloc_seq:
        seat_number += 1
        maximum = alloc["maximum"] if "maximum" in alloc else "N/A"
        contents.append([
            seat_number,
            rules["constituencies"][alloc["const"]]["name"],
            rules["parties"][alloc["party"]],
            alloc["reason"],
            maximum,
        ])
        if has_last:
            last_party_no = alloc["last_party"]
            last_party = "N/A" if last_party_no < 0 else rules["parties"][last_party_no]
            contents[-1].insert(3, last_party)

    return headers, contents, None
