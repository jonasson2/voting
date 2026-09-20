#coding:utf-8
import numpy as np
from numpy import flatnonzero as find
from ties import select_tied


def allocation_step(scores, votes, allocation, divisors, rng=None, on_tie=None):
    """Select among all best list scores and record the pre-allocation quotient."""
    maximum = scores.max()
    if not np.isfinite(maximum):
        raise ValueError("No eligible party-constituency pair can receive the remaining seats.")
    tied = np.flatnonzero(scores == maximum)
    winner = select_tied(tied, maximum, on_tie, rng=rng)
    c, p = np.unravel_index(winner, scores.shape)
    divisor = float(divisors[allocation[c, p]])
    return {
        "constituency": int(c), "party": int(p),
        "maximum": float(maximum), "votes": float(votes[c, p]),
        "divisor": divisor, "quotient": float(votes[c, p] / divisor),
        "tie": bool(len(tied) > 1),
        "lot": bool(len(tied) > 1 and rng is not None),
    }

def common_allocate(
        votes, total_const_seats, total_party_seats, prior_alloc, div_gen,
        compute_criteria, criterion_name, reason, nolast_reason=None, last=None, **kwargs):

    # PREPARE WORK ARRAYS
    # Generic methods treat every constituency-party cell as available.
    votes = np.asarray(votes, dtype=float)
    vote_floor = kwargs.get("vote_floor", 1)
    if vote_floor is not None:
        votes = np.maximum(votes, vote_floor)
    nconst = len(total_const_seats)
    alloc_list = np.asarray(prior_alloc, dtype=int).copy()
    total_party_seats = np.asarray(total_party_seats, dtype=int)
    national_fixed = kwargs.get("nat_prior_allocations")
    if national_fixed is not None:
        total_party_seats = total_party_seats - np.asarray(national_fixed, dtype=int)
    free_const_seats = np.asarray(total_const_seats) - alloc_list.sum(1)
    free_party_seats = total_party_seats - alloc_list.sum(0)
    if (free_const_seats < 0).any() or (free_party_seats < 0).any():
        raise ValueError("Allocation targets are below the seats already allocated.")
    if free_party_seats.sum() < free_const_seats.sum():
        raise ValueError("Party deficits are smaller than the adjustment-seat total.")
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
        openC = find(free_const_seats > 0)
        openP = find(free_party_seats > 0)

        # DETERMINE CRITERION FOR EACH NON-FULL CONSTITUENCY
        scores = np.full(votes.shape, -np.inf)
        has_score = np.zeros(nconst, dtype=bool)
        for c in openC:
            parties = openP
            if kwargs.get("exclude_zero_votes"):
                parties = parties[votes[c, parties] > 0]
            if not len(parties):
                continue
            lp = find(parties==last_party[c])[0] if last_party[c] in parties else None
            (p, score) = compute_criteria(
                votes[c,parties],
                alloc_list[c,parties],
                div,
                votesum = votesum[c],
                nfree = free_const_seats[c],
                totconstseats = total_const_seats[c],
                npartyseats = total_party_seats[parties],
                last_party = lp,
                )
            # A margin is undefined when the sole remaining party has no rival.
            # Criteria may return all tied parties, or one deterministic winner.
            has_score[c] = score is not None
            scores[c, parties[p]] = score if score is not None else 0

        # SELECT CONSTITUENCY AND PARTY WITH MAXIMUM CRITERION
        step = allocation_step(scores, votes, alloc_list, div,
                               kwargs.get("rng"), kwargs.get("on_tie"))
        maxC, maxP = step["constituency"], step["party"]
        previous_party = last_party[maxC]
        last_party[maxC] = maxP
        alloc_list[maxC, maxP] += 1

        step_reason = nolast_reason if has_last and previous_party is None else reason
        if not has_score[maxC]:
            step_reason = "Only party with seats remaining"

        step.update({
            "last_party": previous_party if has_last else None,
            "reason": step_reason,
            "maximum": step["maximum"] if has_score[maxC] else None,
        })
        allocation_sequence.append(step)
        free_const_seats[maxC] -= 1
        free_party_seats[maxP] -= 1
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
        maximum = alloc.get("maximum")
        if maximum is None:
            maximum = "-"
        contents.append([
            seat_number,
            rules["constituencies"][alloc["constituency"]]["name"],
            rules["parties"][alloc["party"]],
            alloc["reason"],
            maximum,
        ])
        if has_last:
            last_party_no = alloc["last_party"]
            last_party = ("N/A" if last_party_no is None or last_party_no < 0
                          else rules["parties"][last_party_no])
            contents[-1].insert(3, last_party)

    return headers, contents, None
