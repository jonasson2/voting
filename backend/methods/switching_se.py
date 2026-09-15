import numpy as np
from ties import select, remap


def _divisors(divisor_gen, count):
    generator = divisor_gen()
    return np.array([next(generator) for _ in range(count + 1)], dtype=float)


def _eligible(shares, threshold):
    return shares * 100 >= threshold


def switching(
        m_votes, v_desired_row_sums, v_desired_col_sums,
        m_prior_allocations, divisor_gen, **kwargs):
    """Return overhang seats and reassign them within their constituencies."""
    votes = np.asarray(m_votes, dtype=float)
    row_totals = np.asarray(v_desired_row_sums, dtype=int)
    party_totals = np.asarray(v_desired_col_sums, dtype=int)
    prior = np.asarray(m_prior_allocations, dtype=int)
    if not np.array_equal(prior.sum(axis=1), row_totals):
        raise ValueError(
            "Swedish switching requires a complete constituency-seat allocation.")

    nat_votes = np.asarray(kwargs.get("nat_votes", votes.sum(axis=0)), dtype=float)
    nat_threshold_total = kwargs.get("nat_threshold_total", nat_votes.sum())
    const_threshold_totals = np.asarray(
        kwargs.get("const_threshold_totals", votes.sum(axis=1)), dtype=float)
    national_threshold = kwargs.get("national_threshold", 0)
    local_threshold = kwargs.get("local_threshold", 0)
    total_seats = kwargs.get("total_seats", int(party_totals.sum()))

    national_shares = (
        nat_votes / nat_threshold_total
        if nat_threshold_total else np.zeros_like(nat_votes)
    )
    nationally_eligible = _eligible(national_shares, national_threshold)
    local_shares = np.divide(
        votes,
        const_threshold_totals[:, None],
        out=np.zeros_like(votes),
        where=const_threshold_totals[:, None] != 0,
    )
    list_eligible = nationally_eligible[None, :] | _eligible(
        local_shares, local_threshold)

    allocation = prior.copy()
    initial = allocation.copy()
    divisors = _divisors(divisor_gen, max(total_seats, int(row_totals.max())))
    vacancies = []
    on_tie = kwargs.get("on_tie")
    for p in np.flatnonzero(allocation.sum(axis=0) > party_totals):
        excess = int(allocation[:, p].sum() - party_totals[p])
        for _ in range(excess):
            removable = (allocation[:, p] > 0) & (row_totals >= 3)
            if not removable.any():
                raise ValueError(
                    f"No removable overhang seat exists for party {p}.")
            quotients = np.full(len(row_totals), np.inf)
            quotients[removable] = (
                votes[removable, p] / divisors[allocation[removable, p] - 1]
            )
            c = select(
                quotients,
                remap(on_tie, np.arange(len(row_totals)) * votes.shape[1] + p)
                if on_tie is not None else None,
                minimum=True)
            removal_quotient = float(quotients[c])
            allocation[c, p] -= 1
            vacancies.append({
                "constituency": c,
                "from": int(p),
                "removal_quotient": removal_quotient,
            })

    switches = []
    while vacancies:
        deficits = party_totals - allocation.sum(axis=0)
        wanting = deficits > 0
        scores = np.full((len(vacancies), votes.shape[1]), -np.inf)
        for vacancy_index, vacancy in enumerate(vacancies):
            c = vacancy["constituency"]
            recipients = wanting & list_eligible[c]
            if not recipients.any():
                continue
            scores[vacancy_index, recipients] = (
                votes[c, recipients] / divisors[allocation[c, recipients]]
            )
        if not np.isfinite(scores).any():
            raise ValueError("A returned Swedish constituency seat cannot be reassigned.")

        report = None
        if on_tie is not None:
            candidates = [v["constituency"] * votes.shape[1] + p
                          for v in vacancies for p in range(votes.shape[1])]
            report = remap(on_tie, candidates)
        vacancy_index, q = np.unravel_index(
            select(scores, report), scores.shape)
        vacancy = vacancies.pop(vacancy_index)
        c = vacancy["constituency"]
        recipient_quotient = float(
            votes[c, q] / divisors[allocation[c, q]])
        allocation[c, q] += 1
        switches.append({
            **vacancy,
            "to": q,
            "recipient_quotient": recipient_quotient,
        })

    stepbystep = {
        "data": {"switches": switches},
        "function": print_switching_table,
        "party_totals": party_totals,
        "seat_changes": allocation - initial,
    }
    return allocation, stepbystep


def print_switching_table(rules, steps):
    headers = [
        "Step", "Constituency", "From", "To",
        "Returned quotient", "Recipient quotient",
    ]
    data = [[
        number,
        rules["constituencies"][switch["constituency"]]["name"],
        rules["parties"][switch["from"]],
        rules["parties"][switch["to"]],
        switch["removal_quotient"],
        switch["recipient_quotient"],
    ] for number, switch in enumerate(steps["switches"], start=1)]
    if not data:
        data = [["–", "–", "No switching required", "–", "–", "–"]]
    return headers, data, "Swedish switching of overhang seats"
