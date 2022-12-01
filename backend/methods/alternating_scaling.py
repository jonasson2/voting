import numpy as np
from numpy import r_
np.set_printoptions(suppress=True, floatmode="fixed", precision=3, linewidth=200)
from apportion import apportion
from copy import deepcopy
global total_iter, total_step
total_iter = 0
total_step = 0
icore = 0

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
            v[:, j] = v[:, j]/sigma
        if np.array_equal(x, y):
            break
    if iter >= 99:
        print('iter: 99 -> Ran through all iterations before breaking')
    return x

def alt_scaling_new(votes, const_seats, party_seats, prior_alloc, div):
    mix_factor_country = 0.5
    mix_factor_const = 0.5
    mix_factor_party = 0.5
    votes = votes.copy().astype(float)
    seats = prior_alloc.copy()
    total_seats = np.sum(const_seats)
    nconst = votes.shape[0]
    nparty = votes.shape[1]
    prior_vector = prior_alloc.flatten()

    # CALCULATE DIVISORS
    #gen = div_gen()
    #N = max(max(const_seats), max(party_seats)) + 1
    #div = np.array([next(gen) for _ in range(N + 1)])
    for iter in range(1, 100):
        # COUNTRY WIDE SCALING
        seats, separator = apportion_equalities(votes.flatten(), prior_vector,
                                                total_seats, div, mix_factor_country)
        seats = seats.reshape((nconst, nparty))
        votes /= separator
        score_min = min(1, separator)

        # CONSTITUENCY SCALING
        for c in range(nconst):
            _, separatorC = apportion_equalities(votes[c,:], prior_alloc[c,:],
                                                const_seats[c], div, mix_factor_const)
            votes[c,:] = votes[c,:]/separatorC

        # PARTY SCALING
        for p in range(nparty):
            # _, separator = apportion_equalities(votes[:,p], prior_alloc[:,p],
            #                                     party_seats[p], div, mix_factor_party)
            _, separatorP = apportion_until_score_min(votes[:,p], prior_alloc[:,p], \
                party_seats[p], div, score_min, mix_factor_party)
            votes[:,p] = votes[:,p]/separatorP

        # CONVERGENCE TEST
        if all(np.sum(seats,1) == const_seats) and all(np.sum(seats,0) <= party_seats):
            break
        if iter == 99:
            print(f'alt_scaling_ineq: No convergence in 99 iterations on core {icore}')
    #seats[0,0] += 1
    stepbystep = {"data": [], "function": print_demo_table}

    return seats, stepbystep

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

    if False: #nat_seats == 0:
        seats = alt_scaling_orig(votes, const_seats, party_seats, prior_alloc, div)
        stepbystep = {"data": [], "function": print_demo_table}
    else:
        seats, stepbystep = alt_scaling_new(votes, const_seats, party_seats, prior_alloc,
                                            div)
    return seats, stepbystep

def alt_scaling_old(m_votes,
                v_desired_row_sums,
                v_desired_col_sums,
                m_prior_allocations,
                divisor_gen,
                party_votes_specified,
                nat_prior_allocations,
                nat_seats,
                **kwargs):
    # ÚRELT
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
        stepbystep = {"data": [], "function": print_demo_table}
        return xp[:-1].tolist() if nat_list_with_seats else xp.tolist(), stepbystep
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
       print('alt_scaling_equalities: No convergence in 99 iterations')
    #else:
    #    print('iter:', iter)
    stepbystep = {"data": [], "function": print_demo_table}
    return (x[:-1].astype(int).tolist() if nat_list_with_seats
            else x.astype(int).tolist()), stepbystep

def print_demo_table(rules, allocation_sequence):
    return [], [], None

def apportion_special(v, xp, max_seats, div): # líklega úrelt
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

def apportion_until_score_min(votes, seats_in, max_seats, div, score_min, mix_factor):
    seats = seats_in.copy()
    if max_seats == 0:
        return seats, np.inf
    score = votes/div[seats]
    if all(score < score_min):
        return seats, score_min  # öll skor < score_min
    while sum(seats) < max_seats:
        k = score.argmax()
        if score[k] < score_min:
            break
        last_score = score[k]
        seats[k] += 1
        score[k] = votes[k]/div[seats[k]]
    k_next = score.argmax()
    score[k_next] = votes[k_next]/div[seats[k_next]]
    separator = (score_min if sum(seats) < max_seats
                 else mix_factor*last_score + (1 - mix_factor)*score[k_next])
    return seats, separator

def apportion_equalities(votes, seats_in, max_seats, div, mix_factor):
    seats = seats_in.copy()
    if sum(seats) >= max_seats:
        return seats, np.inf
    score = votes/div[seats]
    while sum(seats) < max_seats:
        k = score.argmax()
        last_score = score[k]
        seats[k] += 1
        score[k] = votes[k]/div[seats[k]]
    k_next = score.argmax()
    score[k_next] = votes[k_next]/div[seats[k_next]]
    separator = mix_factor*last_score + (1 - mix_factor)*score[k_next]
    return seats, separator

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
