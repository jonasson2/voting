from apportion import apportion1d_general
import numpy as np
from numpy import argmin, flatnonzero as find
from copy import deepcopy

def min_with_index(x, I=None):
    if I is None:
        i = np.argmin(x)
    else:
        i = np.argmin(np.where(I, x, np.inf))
    return (x[i], i)

def max_with_index(x, I=None):
    if I is None:
        i = np.argmax(x)
    else:
        i = np.argmax(np.where(I, x, -np.inf))
    return (x[i], i)

# This function allocates all adjustment seats as if they were fixed.
# It is identical to the first part of the switching function, skipping
# the switch stage.
def adjustment_as_fixed(m_votes,
              v_desired_row_sums,
              v_desired_col_sums,
              m_prior_allocations,
              divisor_gen,
              **kwargs):

    # CREATE NUMPY ARRAYS AND COUNTS FROM PARAMETER LISTS
    votes = np.array(m_votes, float)
    alloc_prior = np.array(m_prior_allocations)
    desired_const = np.array(v_desired_row_sums)
    max_party = np.array(v_desired_col_sums)
    num_constituencies = len(v_desired_row_sums)
    num_parties        = len(v_desired_col_sums)
    assert(sum(max_party) >= sum(desired_const))

    # CALCULATE DIVISORS
    N = max(max(desired_const), max(max_party)) + 1
    div_gen = divisor_gen()
    divisors = np.array([next(div_gen) for i in range(N + 1)])
    
    # ALLOCATE ADJUSTMENT SEATS AS IF THEY WERE FIXED SEATS
    alloc= np.zeros((num_constituencies, num_parties), int)
    temp_votes = deepcopy(votes)
    full = [p for p in range(num_parties) if sum(alloc_prior[:,p]) >= max_party[p]]
    temp_votes[:,full] = 0
    for c in range(num_constituencies):
        alloc_const, _,_ = apportion1d_general(
            v_votes = list(temp_votes[c,:]),
            num_total_seats = desired_const[c],
            prior_allocations = list(alloc_prior[c,:]),
            rule = divisor_gen
        )
        alloc[c,:] = np.array(alloc_const)


    # INFORMATION FOR SECOND STEP-BY-STEP DEMO TABLE
    stepbystep = {
        "data": [],
        "function": []
    }
    return alloc, stepbystep
