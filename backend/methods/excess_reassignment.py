"""Return excess fixed seats and fill the resulting vacancies."""

import numpy as np

from ties import remap, select


def reassign_excess(votes, initial, party_totals, divisor_gen, *,
                    removable_floor, eligible, removable_rows,
                    on_tie=None, rng=None):
    votes = np.asarray(votes, dtype=float)
    allocation = np.asarray(initial, dtype=int).copy()
    party_totals = np.asarray(party_totals, dtype=int)
    floor = np.asarray(removable_floor, dtype=int)
    eligible = np.asarray(eligible, dtype=bool)
    removable_rows = np.asarray(removable_rows, dtype=bool)
    if int(party_totals.sum()) < int(allocation.sum()):
        raise ValueError("Party-seat totals are below the constituency-seat total.")
    if (floor > allocation).any():
        raise ValueError("Removable-seat floors exceed the allocation.")

    generator = divisor_gen()
    divisors = np.array([
        next(generator) for _ in range(int(party_totals.sum()) + 1)
    ], dtype=float)
    vacancies = []
    for p in np.flatnonzero(allocation.sum(axis=0) > party_totals):
        excess = int(allocation[:, p].sum() - party_totals[p])
        for _ in range(excess):
            removable = (allocation[:, p] > floor[:, p]) & removable_rows
            if not removable.any():
                raise ValueError(f"No removable excess seat exists for party {p}.")
            quotients = np.full(allocation.shape[0], np.inf)
            quotients[removable] = (
                votes[removable, p] / divisors[allocation[removable, p] - 1]
            )
            c = select(
                quotients,
                (remap(on_tie, np.arange(allocation.shape[0]) * votes.shape[1] + p)
                 if on_tie is not None else None),
                minimum=True, rng=rng,
            )
            removal_quotient = float(quotients[c])
            allocation[c, p] -= 1
            vacancies.append({
                "constituency": c,
                "from": int(p),
                "removal_quotient": removal_quotient,
            })

    switches = []
    while vacancies:
        wanting = party_totals - allocation.sum(axis=0) > 0
        scores = np.full((len(vacancies), votes.shape[1]), -np.inf)
        for vacancy_index, vacancy in enumerate(vacancies):
            c = vacancy["constituency"]
            recipients = wanting & eligible[c]
            if recipients.any():
                scores[vacancy_index, recipients] = (
                    votes[c, recipients] / divisors[allocation[c, recipients]]
                )
        if not np.isfinite(scores).any():
            raise ValueError("An excess seat cannot be reassigned.")

        report = None
        if on_tie is not None:
            candidates = [v["constituency"] * votes.shape[1] + p
                          for v in vacancies for p in range(votes.shape[1])]
            report = remap(on_tie, candidates)
        vacancy_index, q = np.unravel_index(
            select(scores, report, rng=rng), scores.shape)
        vacancy = vacancies.pop(vacancy_index)
        c = vacancy["constituency"]
        recipient_quotient = float(votes[c, q] / divisors[allocation[c, q]])
        allocation[c, q] += 1
        switches.append({
            **vacancy,
            "to": q,
            "recipient_quotient": recipient_quotient,
        })
    return allocation, switches
