# NumPy version, single constituency hardwired
import sys, numpy as np
from numpy import flatnonzero as find, ix_
from copy import deepcopy
sys.path.append('~/voting/backend/methods')
from alternating_scaling import alt_scaling
from division_rules import sainte_lague_gen

def max_share(votes, max_col_sums):
    voteshare = votes[:,:-1]/np.sum(votes,1)[:,None]
    (nconst, nparty) = np.shape(voteshare)
    col_sum = np.zeros(nparty)
    party = [-1]*nconst
    openC = np.full(nconst, True)
    openP = np.full(nparty, True)
    for n in range(nconst):
        idx = np.argmax(voteshare[ix_(openC, openP)], 1)
        maxparty = find(openP)[idx]
        maxshare = voteshare[openC, maxparty]
        i = np.argmax(maxshare)
        p = maxparty[i]
        const = find(openC)[i]
        party[const] = p
        col_sum[p] += 1
        openC[const] = False
        if col_sum[p] == max_col_sums[p]:
            openP[p] = False
    return party

def max_relative_margin(votes_all, max_col_sums):
    return max_margin(votes_all, max_col_sums, 'relative')

def max_absolute_margin(votes_all, max_col_sums):
    return max_margin(votes_all, max_col_sums, 'absolute')

def max_margin(votes_all, max_col_sums, type):
    votes = votes_all[:,:-1]
    (nconst, nparty) = votes.shape
    col_sum = np.zeros(nparty)
    party = [-1]*nconst
    pmax = np.argmax(votes, axis=1)
    I = range(nconst)
    share_rest = deepcopy(votes)
    share_rest[I, pmax] = -1
    advantage = votes[I, pmax]/np.max(share_rest, axis=1)
    for n in range(nconst):
        const = np.argmax(advantage)
        p = pmax[const]
        party[const] = p
        advantage[const] = -1
        pmax[const] = -1
        col_sum[p] += 1
        if col_sum[p] == max_col_sums[p]:
            C = find(pmax==p)
            for c in C:
                q = np.argmax(share_rest[c,:])
                pmax[c] = q
                share_rest[c, q] = -1
                max_rest = max(share_rest[c,:])
                advantage[c] = (0 if max_rest == 0
                                else votes[c, q]/max_rest if type=='relative'
                                else votes[c, q] - max_rest > 0)
    return party

def scandinavian(votes, _):
    party = np.argmax(votes[:,:-1], 1)
    return party

def optimal_const(votes, max_col_sums):
    (nconst, nparty) = votes.shape
    row_sums = np.ones(nconst, int)
    prior_alloc = np.zeros(votes.shape, int)
    party_votes_specified = True
    nat_prior_allocations = np.zeros(nparty, int)
    nat_seats = int(sum(max_col_sums) - nconst)
    alloc, _ = alt_scaling(votes, row_sums, max_col_sums, prior_alloc, sainte_lague_gen,
                           party_votes_specified, nat_prior_allocations, nat_seats)
    party = [alloc[c].index(1) for c in range(nconst)]
    return party

def apportion_sainte_lague(votes, num_seats, prior_alloc = None):
    n = len(votes)
    if prior_alloc is not None:
        allocations = deepcopy(prior_alloc)
        divisor = 1 + 2*prior_alloc
        divided_votes = votes/divisor[:,None]
    else:
        allocations = np.zeros(n, int)
        divisor = np.ones(n)
        divided_votes = votes.copy()
    for i in range(num_seats):
        p = np.argmax(divided_votes)
        divisor[p] += 2
        divided_votes[p] = votes[p]/divisor[p]
        allocations[p] += 1
    return allocations

def parties_first(votes, p_alloc, _):
    nparty = votes.shape[1] - 1
    alloc = np.zeros(votes.shape, int)
    for p in range(nparty):
        alloc[:,p] = apportion_sainte_lague(votes[:,p], p_alloc[p])
    return alloc

def länder_first(votes, _, c_alloc):
    nconst = votes.shape[0]
    alloc = np.zeros(votes.shape, int)
    for c in range(nconst):
        # skip last party (other)
        alloc[c,:-1] = apportion_sainte_lague(votes[c,:-1], c_alloc[c])
    return alloc


