"""Network LP for increasing marginal seat costs under allocation constraints."""

import numpy as np
# Load before Linux forks workers, avoiding concurrent shared-filesystem imports.
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from common_allocate import prepare_adjustment_bounds


def _constraint_matrices(num_variables, constraints):
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


def allocate_by_marginal_costs(
        row_totals, party_totals, prior, marginal_costs, *, eligible=None,
        nat_prior_allocations=None, name="Seat LP", **kwargs):
    """Minimize separable seat costs on unit-capacity party-to-constituency arcs.

    marginal_costs receives (constituency, party, zero-based seat index) tuples.
    Its costs must be nondecreasing along each list's sequence of seats.
    """
    prior = np.asarray(prior, dtype=int)
    nconst, nparty = prior.shape
    base_rows = prior.sum(axis=1)
    minimums, total, capacities = prepare_adjustment_bounds(
        base_rows, row_totals, kwargs)
    region_groups = kwargs.get("region_groups")
    region_adj_seats = kwargs.get("region_adj_seats")
    if (region_groups is None) != (region_adj_seats is None):
        raise ValueError("Regional groups and adjustment totals must be supplied together.")
    if region_groups is not None:
        region_groups = [np.asarray(group, dtype=int) for group in region_groups]
        region_adj_seats = np.asarray(region_adj_seats, dtype=int)
        members = [int(c) for group in region_groups for c in group]
        if (len(region_groups) != len(region_adj_seats)
                or sorted(members) != list(range(nconst))
                or (region_adj_seats < 0).any()
                or int(region_adj_seats.sum()) != total):
            raise ValueError("Invalid regional adjustment-seat partition or totals.")

    enforce_party_targets = kwargs.get("enforce_party_targets", True)
    has_national_seats = (
        enforce_party_targets and nat_prior_allocations is not None)
    if enforce_party_targets:
        party_targets = np.asarray(party_totals, dtype=int)
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
    for c in range(nconst):
        for p in range(nparty):
            if eligible is not None and not eligible[c, p]:
                continue
            upper = min(int(capacities[c]), int(deficits[p]), total)
            for offset in range(upper):
                index = len(variables)
                final_seat_index = int(prior[c, p]) + offset
                variables.append((c, p, final_seat_index))
                by_constituency[c].append(index)
                by_party[p].append(index)

    if total == 0:
        return prior.copy()
    if not variables:
        raise ValueError(f"{name} has no list that can receive a seat.")

    objective = marginal_costs(variables)

    constraints = []
    all_variables = list(range(len(variables)))
    constraints.append((all_variables, [1] * len(variables), total, total))
    for c, indices in enumerate(by_constituency):
        constraints.append((
            indices, [1] * len(indices),
            int(minimums[c]), int(capacities[c]),
        ))
    if region_groups is not None:
        for group, target in zip(region_groups, region_adj_seats):
            indices = [index for c in group for index in by_constituency[c]]
            constraints.append((indices, [1] * len(indices), int(target), int(target)))
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
        message = f"{name} could not find an allocation: {result.message}"
        if result.status == 2:
            raise ValueError(message)
        raise RuntimeError(message)

    selected = np.rint(result.x).astype(int)
    if not np.allclose(result.x, selected, atol=1e-7):
        raise RuntimeError(f"{name} returned a non-integral allocation.")
    allocation = prior.copy()
    for chosen, (c, p, _) in zip(selected, variables):
        allocation[c, p] += chosen

    added_rows = allocation.sum(axis=1) - base_rows
    added_parties = allocation.sum(axis=0) - prior.sum(axis=0)
    regional_ok = (region_groups is None or all(
        int(added_rows[group].sum()) == int(target)
        for group, target in zip(region_groups, region_adj_seats)))
    if (int(added_rows.sum()) != total
            or (added_rows < minimums).any()
            or (added_rows > capacities).any()
            or (enforce_party_targets and (added_parties > deficits).any())
            or not regional_ok
            or (enforce_party_targets and not has_national_seats
                and not np.array_equal(added_parties, deficits))):
        raise RuntimeError(f"{name} returned an allocation outside its constraints.")
    return allocation
