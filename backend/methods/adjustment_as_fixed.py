import numpy as np
from methods.provisional_allocation import allocate_provisionally

# This function allocates all adjustment seats as if they were fixed.
# It is identical to the first part of the switching function, skipping
# the switch stage.
def adjustment_as_fixed(m_votes,
              v_desired_row_sums,
              v_desired_col_sums,
              m_prior_allocations,
              divisor_gen,
              **kwargs):

    votes = np.maximum(np.asarray(m_votes, dtype=float), 1)
    alloc = allocate_provisionally(
        votes, v_desired_row_sums, v_desired_col_sums,
        m_prior_allocations, divisor_gen, kwargs.get("on_tie"))
    stepbystep = {
        "data": [],
        "function": []
    }
    return alloc, stepbystep
