"""Fill constituency seat totals before enforcing national party totals."""

import numpy as np

from apportion import apportion1d_general
from ties import remap


def allocate_provisionally(votes, row_totals, party_totals, prior,
                           divisor_gen, on_tie=None):
    prior = np.asarray(prior, dtype=int)
    row_totals = np.asarray(row_totals, dtype=int)
    party_totals = np.asarray(party_totals, dtype=int)
    if int(party_totals.sum()) < int(row_totals.sum()):
        raise ValueError("Party-seat totals are below the constituency-seat total.")

    available_votes = np.asarray(votes, dtype=float).copy()
    available_votes[:, prior.sum(axis=0) >= party_totals] = 0
    allocation = prior.copy()
    nparty = allocation.shape[1]
    for c, total in enumerate(row_totals):
        allocation[c], _, _ = apportion1d_general(
            v_votes=available_votes[c],
            num_total_seats=int(total),
            prior_allocations=prior[c],
            rule=divisor_gen,
            on_tie=(remap(on_tie, c * nparty + np.arange(nparty))
                    if on_tie is not None else None),
        )
    return allocation
