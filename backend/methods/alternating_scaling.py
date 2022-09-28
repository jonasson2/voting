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

    nat_list_with_seats = party_votes_specified and nat_seats>sum(nat_prior_allocations)
    if not nat_seats>sum(nat_prior_allocations) and party_votes_specified:
        v_desired_col_sums = [x-y for x,y in zip(v_desired_col_sums,nat_prior_allocations)]
    v = np.array(m_votes, float)
    xp = np.array(m_prior_allocations)
    row_sums = np.array(v_desired_row_sums)
    if nat_list_with_seats :
        v = np.vstack([v, np.ones(len(m_votes[0]))])
        xp = np.vstack([xp, nat_prior_allocations])
        row_sums = np.append(row_sums, nat_seats)
    x = xp.copy()
    y = xp.copy()
    r = row_sums - np.sum(xp, 1)
    c = np.array(v_desired_col_sums) - np.sum(xp, 0)

    if not r.any() and not c.any(): #No iterations as no adj seats to allocate
        return xp[:-1].tolist() if nat_list_with_seats else xp.tolist(), ([], print_demo_table)
    N = max(max(v_desired_row_sums), max(v_desired_col_sums)) + 1
    (nrows, ncols) = np.shape(v)
    div_gen = divisor_gen()
    inverse_divisors = 1/np.array([next(div_gen) for i in range(N + 1)])
    k = -1 if nat_list_with_seats else nrows
    for iter in range(1,100):
        for i in range(nrows):
            if nat_list_with_seats and i == nrows-1:
                pass
            else:
                (x[i,:], rho) = apportion(v[i,:], xp[i,:], r[i], inverse_divisors)
                v[i,:] = v[i,:]*rho
        if nat_list_with_seats :
            p_alloc = x[:-1].sum(axis=0)
            x[-1,:] = [max(0, x)+y for x,y in zip(c - p_alloc, nat_prior_allocations)]
        if iter > 1 and np.array_equal(x, y):
            break
        for j in range(ncols):
            (y[:,j], sigma) = apportion(v[:,j], xp[:,j], c[j], inverse_divisors, nat_list_with_seats)
            v[:k,j] = v[:k,j]*sigma
        if np.array_equal(x, y):
            break
    #Debug
    if iter == 99:
       print('iter: 99 -> Ran through all iterations before breaking')
    #else:
    #    print('iter:', iter)
    return x[:-1].tolist() if nat_list_with_seats else x.tolist(), ([], print_demo_table)
def print_demo_table(rules, allocation_sequence):
    return [], [], None
