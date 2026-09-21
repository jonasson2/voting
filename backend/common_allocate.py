#coding:utf-8
import numpy as np
from numpy import flatnonzero as find
from ties import select_tied


def prepare_adjustment_bounds(base, row_targets, options):
    """Validate adjustment-seat bounds and return finite row capacities."""
    base = np.asarray(base, dtype=int)
    minimums = np.asarray(
        options.get("min_adj_seats", np.asarray(row_targets) - base),
        dtype=int,
    )
    total = int(options.get("num_adjustment_seats", minimums.sum()))
    maxima = options.get("max_adj_seats", minimums)
    if len(minimums) != len(base) or len(maxima) != len(base):
        raise ValueError("Adjustment-seat bounds do not match the constituencies.")
    if (minimums < 0).any():
        raise ValueError("Adjustment-seat minimums must be non-negative.")
    if total < int(minimums.sum()):
        raise ValueError("Constituency minimums exceed the adjustment-seat total.")
    if any(maximum is not None and maximum < minimum
           for minimum, maximum in zip(minimums, maxima)):
        raise ValueError(
            "An adjustment-seat maximum is below its constituency minimum.")
    capacity = np.array([
        total if maximum is None else maximum for maximum in maxima
    ], dtype=int)
    if int(capacity.sum()) < total:
        raise ValueError(
            "Constituency maxima prevent allocation of all adjustment seats.")
    return minimums, total, capacity


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

def allocate_fixed(
        votes, total_const_seats, total_party_seats, prior_alloc, div_gen,
        compute_criteria, criterion_name, reason, nolast_reason=None, last=None, **kwargs):
    """Allocate seats to predetermined constituency row totals."""

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


def common_allocate(
        votes, row_targets, party_targets, prior_alloc, div_gen,
        criterion, criterion_name, reason, *, flex_scores=None, **kwargs):
    """Coordinate fixed constituency minima and an optional bounded pool."""
    from allocate_pool import allocate_pool

    votes = np.asarray(votes, dtype=float)
    vote_floor = kwargs.get("vote_floor", 1)
    if vote_floor is not None:
        votes = np.maximum(votes, vote_floor)
    prior = np.asarray(prior_alloc, dtype=int)
    base = prior.sum(axis=1)
    minimums, total, capacity = prepare_adjustment_bounds(
        base, row_targets, kwargs)

    targets = np.asarray(party_targets, dtype=int)
    national_fixed = kwargs.get("nat_prior_allocations")
    if national_fixed is not None:
        targets = targets - np.asarray(national_fixed, dtype=int)
    deficits = targets - prior.sum(axis=0)
    if (deficits < 0).any():
        raise ValueError("Adjustment seats cannot resolve a party excess.")
    if int(deficits.sum()) < total:
        raise ValueError(
            "Party deficits are smaller than the adjustment-seat total.")

    options = {key: kwargs.get(key) for key in ("rng", "on_tie")}
    options["exclude_zero_votes"] = kwargs.get("exclude_zero_votes", False)
    fixed_options = options.copy()
    if flex_scores is None:
        fixed_options.update(
            nolast_reason=kwargs.get("nolast_reason"),
            last=kwargs.get("last"),
        )
    allocation, demo = allocate_fixed(
        votes, base + minimums, targets, prior, div_gen,
        criterion, criterion_name, reason, vote_floor=None,
        **fixed_options)
    steps = demo["data"]["sequence"]
    for step in steps:
        step["phase"] = "minimum"

    remaining = total - int(minimums.sum())
    if remaining:
        if flex_scores is None:
            raise ValueError(
                "This allocation method does not define a bounded-pool score.")
        allocation, extra = allocate_pool(
            votes, base + capacity, targets, allocation, div_gen,
            remaining, flex_scores, reason, **options)
        steps.extend(extra)
        if minimums.any():
            for step in steps:
                phase = (
                    "Constituency minimum"
                    if step["phase"] == "minimum" else "Remaining pool")
                step["reason"] = f'{phase}: {reason}'

    added = allocation.sum(axis=1) - base
    if (int(added.sum()) != total or (added < minimums).any()
            or (added > capacity).any()
            or (allocation.sum(axis=0) > targets).any()):
        raise RuntimeError(
            "Adjustment-seat allocation violated its totals or bounds.")
    return allocation, demo


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
