import numpy as np
from numpy import r_
np.set_printoptions(suppress=True, floatmode="fixed", precision=3, linewidth=200)
from apportion import apportion

global total_iter, total_step
total_iter = 0
total_step = 0

def alt_scaling_orig(v, const_seats, party_seats, prior_alloc, div):
        x = prior_alloc.copy()
        y = prior_alloc.copy()
        r = const_seats - np.sum(x, 1)
        c = party_seats - np.sum(x, 0)
        (nrows, ncols) = v.shape
        for iter in range(1, 100):
            for i in range(nrows):
                (x[i, :], rho) = apportion_orig(v[i, :], prior_alloc[i, :], r[i], div)
                v[i, :] = v[i, :]/rho
            if iter > 1 and np.array_equal(x, y):
                break
            for j in range(ncols):
                (y[:, j], sigma) = apportion_orig(v[:, j], prior_alloc[:, j], c[j], div)
                if sigma==0:
                    pass
                v[:, j] = v[:, j]/sigma
            if np.array_equal(x, y):
                break
        if iter >= 99:
            print('iter: 99 -> Ran through all iterations before breaking')
        return x

def alt_scaling_new(votes, const_seats, party_seats, prior_alloc, div):
    ncols = votes.shape[1]
    xp = prior_alloc
    #const_seats = np.append(const_seats, nat_seats)
    nrows = votes.shape[0]
    x = xp.copy()
    y = xp.copy()
    r = const_seats - np.sum(xp, 1)
    c = party_seats - np.sum(xp, 0)

    if not r.any() and not c.any():  # No iterations as no adj seats to allocate
        return xp
    for iter in range(1, 100):
        for i in range(nrows):
            (x[i, :], rho) = apportion_orig(votes[i, :], xp[i, :], r[i], div)
            votes[i, :] = votes[i, :]/rho
        if iter > 1 and np.array_equal(x, y):
            break
        for j in range(ncols):
            (y[:, j], sigma) = apportion_special(votes[:, j], xp[:, j], c[j], div)
            votes[:, j] = votes[:, j]/sigma
        if np.array_equal(x, y):
            break
    # Debug
    print('iter =', iter)
    if iter == 99:
        print('iter: 99 -> Ran through all iterations before breaking')
    return x

    # else:
    #    print('iter:', iter)

def alt_scaling(m_votes,
                v_desired_row_sums,
                v_desired_col_sums,
                m_prior_allocations,
                divisor_gen,
                nat_prior_allocations = None,
                **kwargs):

    # COPY PARAMETERS TO NUMPY ARRAYS
    const_seats = np.array(v_desired_row_sums, int)
    votes = np.array(m_votes, float)
    (nrows, ncols) = np.shape(votes)
    prior_alloc = np.array(m_prior_allocations, int)
    nat_prior_alloc = (np.zeros(ncols, int) if nat_prior_allocations is None
                       else np.array(nat_prior_allocations, int))
    party_seats = np.array(v_desired_col_sums) - nat_prior_alloc
    nat_seats = sum(party_seats) - sum(const_seats)
    div_gen = divisor_gen()
    N = max(max(const_seats), max(party_seats)) + 1
    div = np.array([next(div_gen) for i in range(N + 1)])

    if nat_seats == 0:
        x = alt_scaling_orig(votes, const_seats, party_seats, prior_alloc, div)
    else:
        x = alt_scaling_new(votes, const_seats, party_seats, prior_alloc, div)
    return (x.astype(int).tolist(), ([], print_demo_table))

def alt_scaling_old(m_votes,
                v_desired_row_sums,
                v_desired_col_sums,
                m_prior_allocations,
                divisor_gen,
                party_votes_specified,
                nat_prior_allocations,
                nat_seats,
                **kwargs):
    nat_list_with_seats = party_votes_specified and nat_seats > sum(nat_prior_allocations)
    if not nat_seats > sum(nat_prior_allocations) and party_votes_specified:
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
        #print('iter=',iter)
        for i in range(nrows):
            if nat_list_with_seats and i == nrows-1:
                pass
            else:
                (x[i,:], rho) = apportion_special(v[i,:], xp[i,:], r[i], inverse_divisors)
                v[i,:] = v[i,:]*rho
        if nat_list_with_seats :
            p_alloc = x[:-1].sum(axis=0)
            x[-1,:] = [max(0, x)+y for x,y in zip(c - p_alloc, nat_prior_allocations)]
        if iter > 1 and np.array_equal(x, y):
            break
        for j in range(ncols):
            #print('j=',j)
            (y[:,j], sigma) = apportion_special(v[:,j], xp[:,j], c[j], inverse_divisors,
                                         nat_list_with_seats)
            v[:k,j] = v[:k,j]*sigma
        if np.array_equal(x, y):
            break
    #Debug
    #print('iter =', iter)
    if iter == 99:
       print('iter: 99 -> Ran through all iterations before breaking')
    #else:
    #    print('iter:', iter)
    return x[:-1].astype(int).tolist() \
               if nat_list_with_seats \
               else x.astype(int).tolist(), ([], print_demo_table)

def print_demo_table(rules, allocation_sequence):
    return [], [], None

def apportion_special(v, xp, max_seats, div):
    x = xp.copy()
    if max_seats == 0:
        return x, np.inf
    for i in range(max_seats):
        vdiv = r_[v/div[x], 1.0]
        k = vdiv.argmax()
        if k < len(x):
            x[k] += 1
    vdivnext = max(r_[v/div[x], 1.0])
    return x, (vdiv[k] + vdivnext)/2

def apportion_orig(v, xp, total_seats, div):
    x = xp.copy()
    if total_seats == 0:
        return x, np.inf
    for i in range(total_seats):
        vdiv = v/div[x]
        k = vdiv.argmax()
        x[k] += 1
    vdivnext = max(v/div[x])
    return x, (vdiv[k] + vdivnext)/2
