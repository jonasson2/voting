"""Maximum-entropy adjustment-seat allocation using a network LP."""

import numpy as np

from common_allocate import prepare_adjustment_bounds


def _divisors(divisor_gen, count):
    generator = divisor_gen()
    values = np.array([next(generator) for _ in range(count)], dtype=float)
    if (not np.isfinite(values).all() or (values <= 0).any()
            or (np.diff(values) < 0).any()):
        raise ValueError(
            "Optimal LP requires positive, finite, nondecreasing divisors.")
    return values


def _constraint_matrices(num_variables, constraints):
    from scipy.sparse import coo_matrix

    equalities = []
    inequalities = []
    for indices, coefficients, low, high in constraints:
        if low == high:
            equalities.append((indices, coefficients, high))
            continue
        if np.isfinite(high):
            inequalities.append((indices, coefficients, high))
        if np.isfinite(low):
            inequalities.append((
                indices, [-value for value in coefficients], -low,
            ))

    def matrix(rows):
        row_indices = []
        columns = []
        values = []
        right_hand_side = []
        for row, (indices, coefficients, bound) in enumerate(rows):
            row_indices.extend([row] * len(indices))
            columns.extend(indices)
            values.extend(coefficients)
            right_hand_side.append(bound)
        if not rows:
            return None, None
        return (
            coo_matrix(
                (values, (row_indices, columns)),
                shape=(len(rows), num_variables),
            ).tocsr(),
            np.asarray(right_hand_side),
        )

    inequality_matrix, inequality_bounds = matrix(inequalities)
    equality_matrix, equality_bounds = matrix(equalities)
    return (inequality_matrix, inequality_bounds,
            equality_matrix, equality_bounds)


def optimal_lp(
        m_votes, v_desired_row_sums, v_desired_col_sums,
        m_prior_allocations, divisor_gen, nat_prior_allocations=None,
        **kwargs):
    """Maximize divisor-rule entropy within row and optional party bounds."""
    from scipy.optimize import linprog

    votes = np.maximum(np.asarray(m_votes, dtype=float), 1)
    prior = np.asarray(m_prior_allocations, dtype=int)
    if votes.shape != prior.shape:
        raise ValueError("Votes and prior allocations must have the same shape.")

    nconst, nparty = votes.shape
    base_rows = prior.sum(axis=1)
    minimums, total, capacities = prepare_adjustment_bounds(
        base_rows, v_desired_row_sums, kwargs)

    enforce_party_targets = kwargs.get("enforce_party_targets", True)
    has_national_seats = (
        enforce_party_targets and nat_prior_allocations is not None)
    if enforce_party_targets:
        party_targets = np.asarray(v_desired_col_sums, dtype=int)
        if has_national_seats:
            party_targets = (
                party_targets - np.asarray(nat_prior_allocations, dtype=int))
        deficits = party_targets - prior.sum(axis=0)
        if (deficits < 0).any():
            raise ValueError("Party targets are below seats already allocated.")
        if int(deficits.sum()) < total:
            raise ValueError(
                "Party deficits are smaller than the adjustment-seat total.")
        if not has_national_seats and int(deficits.sum()) != total:
            raise ValueError(
                "Party deficits do not equal the adjustment-seat total.")
    else:
        deficits = np.full(nparty, total, dtype=int)

    variables = []
    by_constituency = [[] for _ in range(nconst)]
    by_party = [[] for _ in range(nparty)]
    max_final_seats = int(prior.max(initial=0))
    for c in range(nconst):
        for p in range(nparty):
            upper = min(int(capacities[c]), int(deficits[p]), total)
            for offset in range(upper):
                index = len(variables)
                final_seat_index = int(prior[c, p]) + offset
                variables.append((c, p, final_seat_index))
                by_constituency[c].append(index)
                by_party[p].append(index)
                max_final_seats = max(max_final_seats, final_seat_index + 1)

    if total == 0:
        return prior.copy(), {"data": [], "function": print_demo_table}
    if not variables:
        raise ValueError("Optimal LP has no list that can receive a seat.")

    divisors = _divisors(divisor_gen, max_final_seats)
    objective = -np.array([
        np.log(votes[c, p] / divisors[seat_index])
        for c, p, seat_index in variables
    ])

    constraints = []
    all_variables = list(range(len(variables)))
    constraints.append((all_variables, [1] * len(variables), total, total))
    for c, indices in enumerate(by_constituency):
        constraints.append((
            indices, [1] * len(indices),
            int(minimums[c]), int(capacities[c]),
        ))
    if enforce_party_targets:
        for p, indices in enumerate(by_party):
            target = int(deficits[p])
            if target == 0:
                continue
            lower = 0 if has_national_seats else target
            constraints.append((indices, [1] * len(indices), lower, target))
    (inequality_matrix, inequality_bounds,
     equality_matrix, equality_bounds) = _constraint_matrices(
         len(variables), constraints)
    # These are unit-capacity arcs from parties to constituencies. The
    # resulting network-flow polytope has integral vertices, so HiGHS can
    # solve the continuous LP without branch-and-bound. Nondecreasing
    # marginal costs also make explicit seat-order constraints unnecessary.
    result = linprog(
        c=objective,
        A_ub=inequality_matrix,
        b_ub=inequality_bounds,
        A_eq=equality_matrix,
        b_eq=equality_bounds,
        bounds=(0, 1),
        method="highs",
        options={"presolve": False},
    )
    if not result.success:
        message = f"Optimal LP could not find an allocation: {result.message}"
        if result.status == 2:
            raise ValueError(message)
        raise RuntimeError(message)

    selected = np.rint(result.x).astype(int)
    if not np.allclose(result.x, selected, atol=1e-7):
        raise RuntimeError("Optimal LP returned a non-integral allocation.")
    allocation = prior.copy()
    for chosen, (c, p, _) in zip(selected, variables):
        allocation[c, p] += chosen

    added_rows = allocation.sum(axis=1) - base_rows
    added_parties = allocation.sum(axis=0) - prior.sum(axis=0)
    if (int(added_rows.sum()) != total
            or (added_rows < minimums).any()
            or (added_rows > capacities).any()
            or (enforce_party_targets and (added_parties > deficits).any())
            or (enforce_party_targets and not has_national_seats
                and not np.array_equal(added_parties, deficits))):
        raise RuntimeError("Optimal LP returned an allocation outside its constraints.")
    return allocation, {"data": [], "function": print_demo_table}


def print_demo_table(rules, data):
    return [], [], None
