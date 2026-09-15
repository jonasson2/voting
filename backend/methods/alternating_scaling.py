import numpy as np
from randomness import make_rng, random_uniform
np.set_printoptions(suppress=True, floatmode="fixed", precision=3, linewidth=200)
from apportion import apportion
from copy import deepcopy
global total_iter, total_step
total_iter = 0
total_step = 0
icore = 0

def alt_scaling_orig(v, const_seats, party_seats, prior_alloc, div, rng):
    x = prior_alloc.copy()
    r = const_seats - np.sum(x, 1)
    c = party_seats - np.sum(x, 0)
    (nrows, ncols) = v.shape
    y = x.copy()
    xsaved = x.copy()
    
    Niter = 20
    for iter in range(1, Niter):
        print("iter=",iter)
        for i in range(nrows):
            (x[i, :], rho) = apportion_orig(
                v[i, :], xsaved[i, :], r[i], div, rng)
            v[i, :] = v[i, :]/rho
            print(f"i: {i}, rho:{rho:.10f}")
        if iter > 1 and np.array_equal(x, y):
            break
        for j in range(ncols):
            (y[:, j], sigma) = apportion_orig(
                v[:, j], xsaved[:, j], c[j], div, rng)
            v[:, j] = v[:, j]/sigma
            print(f"i: {i}, sigma:{sigma:.10f}")
        if np.array_equal(x, y):
            break
    if iter >= Niter:
        print('Ran through all iterations before breaking')
    print('votes:', v)
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
    # This generic method treats every constituency-party cell as available.
    votes = np.maximum(np.asarray(m_votes, dtype=float), 1)
    (nrows, ncols) = np.shape(votes)
    prior_alloc = np.array(m_prior_allocations, int)
    nat_prior_alloc = (np.zeros(ncols, int) if nat_prior_allocations is None
                       else np.array(nat_prior_allocations, int))
    party_seats = np.array(v_desired_col_sums) - nat_prior_alloc
    nat_seats = sum(party_seats) - sum(const_seats)
    div_gen = divisor_gen()
    rng = kwargs.get("rng") or make_rng()
    N = max(max(const_seats), max(party_seats)) + 1
    div = np.array([next(div_gen) for i in range(N + 1)])

    if nat_seats == 0:
        seats = alt_scaling_orig(votes, const_seats, party_seats, prior_alloc, div, rng)
        stepbystep = {"data": [], "function": print_demo_table}
    else:
        seats, stepbystep = alt_scaling_new(votes, const_seats, party_seats, prior_alloc,
                                            div)
    return seats, stepbystep

def print_demo_table(rules, allocation_sequence):
    return [], [], None

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

def apportion_orig(v, xp, total_seats, div, rng):
    x = xp.copy()
    if total_seats == 0:
        return x, np.inf
    for i in range(total_seats):
        vdiv = v/div[x]
        k = vdiv.argmax()
        x[k] += 1
    vdivnext = max(v/div[x])
    return x, (random_uniform(rng, vdivnext, vdiv[k])
               + 0.00001 * random_uniform(rng, 0, 1))
    # return x, (vdiv[k] + vdivnext)/2
