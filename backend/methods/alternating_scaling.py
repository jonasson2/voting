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
                nat_prior_allocations,
                nat_seats,
                **kwargs):
    import numpy as np
    v = np.array(m_votes, float)
    xp = np.array(m_prior_allocations)
    row_sums = np.array(v_desired_row_sums)
    if party_votes_specified:
        v = np.vstack([v, np.ones(len(m_votes[0]))])
        xp = np.vstack([xp, nat_prior_allocations])
        row_sums = np.append(row_sums, nat_seats)
    x = xp.copy()
    y = xp.copy()
    r = row_sums - np.sum(xp, 1)
    c = np.array(v_desired_col_sums) - np.sum(xp, 0)

    if not r.any() and not c.any():
        print('No iterations as no seats adj seats to allocate')
        return xp[:-1].tolist() if party_votes_specified else xp.tolist(), ([], print_demo_table)
    N = max(max(v_desired_row_sums), max(v_desired_col_sums)) + 1
    (nrows, ncols) = np.shape(v)
    div_gen = divisor_gen()
    inverse_divisors = 1/np.array([next(div_gen) for i in range(N + 1)])
    k = -1 if party_votes_specified else nrows

    for iter in range(1,100):
        for i in range(nrows):
            if party_votes_specified and i == nrows-1:
                pass
            else:
                (x[i,:], rho) = apportion(v[i,:], xp[i,:], r[i], inverse_divisors)
                v[i,:] = v[i,:]*rho
        if party_votes_specified:
            p_alloc = x.sum(axis=0)
            x[-1,:] = [max(0, x) for x in c - p_alloc]
        if iter > 1 and np.array_equal(x, y):
            break
        for j in range(ncols):
            (y[:,j], sigma) = apportion(v[:,j], xp[:,j], c[j], inverse_divisors, party_votes_specified)
            v[:k,j] = v[:k,j]*sigma
        if np.array_equal(x, y):
            break
    #Debug
    if iter == 99:
        print('Ran through all iterations before breaking')
    else:
        print('iter:', iter)
    return x[:-1].tolist() if party_votes_specified else x.tolist(), ([], print_demo_table)

def print_demo_table(rules, allocation_sequence):
    return [], [], None
