"""Shared row and column scaling of fractional reference seats."""

import numpy as np

REFERENCE_SCALING_TOLERANCE = 1e-8


def _scale_to_rows(matrix, row_sums):
    current = matrix.sum(axis=1)
    factors = np.divide(
        row_sums, current, out=np.ones_like(row_sums, dtype=float),
        where=current != 0)
    matrix *= factors[:, None]


def _scale_to_columns(matrix, column_sums):
    current = matrix.sum(axis=0)
    factors = np.divide(
        column_sums, current, out=np.ones_like(column_sums, dtype=float),
        where=current != 0)
    matrix *= factors[None, :]


def _scale_to_both_margins(matrix, row_sums, column_sums, total_seats):
    equal_margins = np.isclose(row_sums.sum(), column_sums.sum())
    for _ in range(10000):
        _scale_to_rows(matrix, row_sums)
        current_columns = matrix.sum(axis=0)
        if equal_margins:
            _scale_to_columns(matrix, column_sums)
            row_error = np.max(np.abs(matrix.sum(axis=1) - row_sums))
            if row_error <= REFERENCE_SCALING_TOLERANCE:
                return
            continue

        over = current_columns > column_sums + REFERENCE_SCALING_TOLERANCE
        if not over.any():
            return
        for party in np.flatnonzero(over):
            matrix[:, party] *= column_sums[party] / current_columns[party]
        available = total_seats - column_sums[over].sum()
        current = matrix[:, ~over].sum()
        if current:
            matrix[:, ~over] *= available / current
    raise RuntimeError(
        'Reference seat share scaling did not converge. This may happen when '
        'isolated parties or constituencies, such as Åland, make party and '
        'constituency totals incompatible. Try "within constituencies" scaling.'
    )

