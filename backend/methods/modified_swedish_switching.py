"""Recipients-first Swedish-style switching with feasible greedy choices."""

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow

from methods.constituency_optimal import prepare_baseline
from methods.provisional_allocation import divisor_values
from methods.swedish_style_switching import print_removal_table
from methods.switching_tables import print_initial_allocation
from ties import select_tied


def _can_remove(capacity, surplus, required):
    """Can donor parties supply the removals required in these constituencies?

    During additions, required is a lower bound on eventual removals. During
    removals its sum equals the remaining surplus, so every margin must be met.
    """
    total = int(required.sum())
    if total == 0:
        return True
    if total > surplus.sum() or (required > capacity.sum(axis=1)).any():
        return False
    nconst, nparty = capacity.shape
    graph = np.zeros((nparty + nconst + 2,) * 2, dtype=np.int64)
    graph[0, 1:nparty + 1] = surplus
    graph[1:nparty + 1, nparty + 1:-1] = capacity.T
    graph[nparty + 1:-1, -1] = required
    return maximum_flow(csr_matrix(graph), 0, len(graph) - 1).flow_value == total


def _choose(scores, feasible, on_tie, *, minimum=False):
    """Choose the first best feasible list, reporting only eligible ties."""
    flat = scores.ravel()
    tied = []
    for index in np.argsort(flat if minimum else -flat, kind="stable"):
        if not np.isfinite(flat[index]) or (tied and flat[index] != flat[tied[0]]):
            break
        if feasible(int(index)):
            if on_tie is None:
                return np.unravel_index(index, scores.shape)
            tied.append(int(index))
    if not tied:
        raise RuntimeError("Modified Swedish switching has no feasible continuation.")
    index = select_tied(tied, float(flat[tied[0]]), on_tie)
    return np.unravel_index(index, scores.shape)


def switching(votes, row_totals, party_totals, prior, divisor_gen, **kwargs):
    prior = np.asarray(prior, dtype=int)
    votes, rows, targets, baseline = prepare_baseline(
        votes, row_totals, party_totals, prior, divisor_gen, kwargs)
    allocation = baseline.copy()
    difference = baseline.sum(axis=0) - targets
    surplus, deficit = np.maximum(difference, 0), np.maximum(-difference, 0)
    capacity = np.where((difference > 0)[None, :], baseline - prior, 0)
    excess = np.zeros(len(rows), dtype=int)
    divisors = divisor_values(divisor_gen, int(rows.max(initial=0)))
    on_tie = kwargs.get("on_tie")
    steps = {
        "initial_allocation": [
            {"party": p, "goal": int(targets[p]), "actual": int(actual)}
            for p, actual in enumerate(baseline.sum(axis=0))],
        "additions": [], "removals": [],
    }

    while deficit.any():
        scores = votes / divisors[allocation]
        scores[:, deficit == 0] = -np.inf
        scores[excess >= capacity.sum(axis=1), :] = -np.inf
        checked = {}

        def can_add(index):
            c, _ = np.unravel_index(index, scores.shape)
            if c not in checked:
                excess[c] += 1
                checked[c] = _can_remove(capacity, surplus, excess)
                excess[c] -= 1
            return checked[c]

        c, p = _choose(scores, can_add, on_tie)
        steps["additions"].append({
            "constituency": int(c), "to": int(p),
            "recipient_quotient": float(scores[c, p]),
        })
        allocation[c, p] += 1
        deficit[p] -= 1
        excess[c] += 1

    while surplus.any():
        scores = votes / divisors[np.maximum(allocation - 1, 0)]
        scores[(capacity == 0) | (surplus == 0)[None, :]
               | (excess == 0)[:, None]] = np.inf

        def can_remove(index):
            c, p = np.unravel_index(index, scores.shape)
            capacity[c, p] -= 1
            surplus[p] -= 1
            excess[c] -= 1
            possible = _can_remove(capacity, surplus, excess)
            capacity[c, p] += 1
            surplus[p] += 1
            excess[c] += 1
            return possible

        c, p = _choose(scores, can_remove, on_tie, minimum=True)
        steps["removals"].append({
            "constituency": int(c), "from": int(p),
            "removal_quotient": float(scores[c, p]),
        })
        allocation[c, p] -= 1
        capacity[c, p] -= 1
        surplus[p] -= 1
        excess[c] -= 1

    lower = np.where((difference > 0)[None, :], prior, baseline)
    upper = np.where((difference < 0)[None, :], rows[:, None], baseline)
    if ((allocation < lower).any() or (allocation > upper).any()
            or not np.array_equal(allocation.sum(axis=0), targets)
            or not np.array_equal(allocation.sum(axis=1), rows)):
        raise RuntimeError("Modified Swedish switching violated seat constraints.")
    return allocation, {
        "data": steps,
        "functions": [print_initial_allocation, print_additions, print_removal_table],
    }


def print_additions(system, steps):
    headers = ["No.", "Constituency", "To", "Recipient quotient"]
    rows = [[number,
             system["constituencies"][seat["constituency"]]["name"],
             system["parties"][seat["to"]], seat["recipient_quotient"]]
            for number, seat in enumerate(steps["additions"], 1)]
    if not rows:
        rows = [["–", "–", "No missing seats", "–"]]
    return headers, rows, "Addition of missing adjustment seats"
