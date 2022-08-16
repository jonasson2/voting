from apportion import apportion
from copy import deepcopy

import numpy as np

global total_iter, total_step
total_iter = 0
total_step = 0

def alt_scaling(m_votes,
                v_desired_row_sums,
                v_desired_col_sums,
                m_prior_allocations,
                divisor_gen,
                party_votes_specified,
                **kwargs):
    import numpy as np
    v = np.array(m_votes, float)
    xp = np.array(m_prior_allocations)
    x = xp.copy()
    y = xp.copy()
    r = np.array(v_desired_row_sums) - np.sum(xp, 1)
    c = np.array(v_desired_col_sums) - np.sum(xp, 0)
    N = max(max(v_desired_row_sums), max(v_desired_col_sums)) + 1
    (nrows, ncols) = np.shape(v)
    div_gen = divisor_gen()
    inverse_divisors = 1/np.array([next(div_gen) for i in range(N + 1)])
    for iter in range(1,100):
        for i in range(nrows):
            (x[i,:], rho) = apportion(v[i,:], xp[i,:], r[i], inverse_divisors)
            v[i,:] = v[i,:]*rho
        if iter > 1 and np.array_equal(x, y):
            break
        for j in range(ncols):
            (y[:,j], sigma) = apportion(v[:,j], xp[:,j], c[j], inverse_divisors)
            v[:,j] = v[:,j]*sigma
        if np.array_equal(x, y):
            break
    return x.tolist(), ([], print_demo_table)

def print_demo_table(rules, allocation_sequence):
    return [], [], None
