# NumPy version, single constituency hardwired
import sys, numpy as np
from numpy import flatnonzero as find, ix_
from copy import deepcopy
sys.path.append('~/voting/backend/methods')
from alternating_scaling import alt_scaling
from division_rules import sainte_lague_gen
from methods.common_methods import max_absolute_margin
from methods.common_methods import max_relative_margin

#import gurobipy

def find_first(p):
    return np.argmax(p)

def votepct_const(votes, party_seats):
    voteshare = votes[:,:-1]/np.sum(votes,1)[:,None]
    (nconst, nparty) = np.shape(voteshare)
    col_sum = np.zeros(nparty)
    party = [None]*nconst
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
        if col_sum[p] == party_seats[p]:
            openP[p] = False
    return party

def pos_n_largest(x, select, n):
    # return the positions of the n largest elements in x
    if n >= sum(select):
        return find(select)
    else:
        large = np.argpartition(x[select], -n)[-n:]
        return find(select)[large]

def ampel_const(votes, party_seats):
    # Returns list of parties that are allocated the seat in each constituency
    voteshare = votes[:,:-1]/np.sum(votes,1)[:,None]
    (nconst, nparty) = np.shape(voteshare)
    n_available_seats = party_seats.copy()
    party = np.zeros(nconst, int)
    openC = np.full(nconst, True)
    openP = np.full(nparty, True)
    while any(openC):
        share = voteshare[ix_(openC, openP)]
        maxshare = share.max(1)[:,None]
        largest = np.argmax(share == maxshare, 1)
        P = find(openP)
        C = find(openC)
        [nC, nP] = share.shape
        is_largest = np.full((nC, nP), False)
        is_largest[range(nC), largest] = True
        for (j,p) in enumerate(P):
            i = pos_n_largest(share[:,j], is_largest[:,j], n_available_seats[p])
            C_to_allocate = C[i]
            party[C_to_allocate] = p
            n_available_seats[p] -= len(C_to_allocate)
            openC[C_to_allocate] = False
            if n_available_seats[p] <= 0:
                openP[p] = False
    return party

def rel_margin_const(votes, party_seats):
    return max_margin(votes, party_seats, 'relative')

def abs_margin_const(votes_all, party_seats):
    return max_margin(votes_all, party_seats, 'absolute')

def max_margin(votes, party_seats, type):
    (nconst, nparty) = votes.shape
    assert(party_seats.sum() >= nconst)
    allocated = np.zeros(nparty)
    openP = [p for p in range(nparty) if party_seats[p] > 0]
    openC = list(range(nconst))
    selected = [None]*nconst
    while openC:
        margin = np.zeros(len(openC))
        jmax = np.zeros(len(openC), int)
        for (k,c) in enumerate(openC):
            v = votes[c, openP]
            j = v.argmax()
            if len(v) > 1:
                if type=='absolute':
                    margin[k] = (v[j] - np.delete(v, j)).min()
                else: #type=='relative'
                    margin[k] = (v[j]/np.maximum(1e-10, np.delete(v, j))).min()
            jmax[k] = j
        kmax = margin.argmax()
        cmax = openC[kmax]
        pmax = openP[jmax[kmax]]
        selected[cmax] = pmax
        allocated[pmax] += 1
        openC.remove(cmax)
        if allocated[pmax] == party_seats[pmax]:
            openP.remove(pmax)
    return selected

    # advantage = votes[I, pmax]/np.max(share_rest, axis=1)
    # while any(free_seats):
    #     const = np.argmax(advantage)
    #     p = pmax[const]
    #     party[const] = p
    #     advantage[const] = -1
    #     pmax[const] = -1
    #     col_sum[p] += 1
    #     if col_sum[p] == party_seats[p]:
    #         C = find(pmax==p)
    #         for c in C:
    #             q = np.argmax(share_rest[c,:])
    #             pmax[c] = q
    #             share_rest[c, q] = -1
    #             max_rest = max(share_rest[c,:])
    #             advantage[c] = (0 if max_rest == 0
    #                             else votes[c, q]/max_rest if type=='relative'
    #                             else votes[c, q] - max_rest > 0)
    # return party

def scandinavian(votes, _):
    party = np.argmax(votes[:,:-1], 1)
    return party

def optimal_const(votes, party_seats):
    (nconst, nparty) = votes.shape
    row_sums = np.ones(nconst, int)
    prior_alloc = np.zeros(votes.shape, int)
    alloc, _ = alt_scaling(votes, row_sums, party_seats, prior_alloc, sainte_lague_gen)
    party = [np.argmax(alloc[c]) for c in range(nconst)]
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

# def gurobi_optimal_const(votes, party_seats):
#     from gurobipy import Model, quicksum, GRB
#     (NC, NP) = votes.shape
#     P = range(NP)
#     C = range(NC)
#     m = Model()
#     zerovotes = np.where(votes > 0, 1, 0)
#     x = m.addMVar((NC, NP), vtype='B', ub=zerovotes)
#     m.addConstrs((sum(x[:,p]) <= party_seats[p] for p in P))
#     m.addConstrs((sum(x[c,:]) == 1 for c in C))
#     A = np.log(np.where(votes > 0, votes, 1))
#     m.setObjective(quicksum(A[c,p]*x[c,p] for p in P for c in C), sense=GRB.MAXIMIZE)
#     m.setParam('OutputFlag', False)
#     m.optimize()
#     if m.status == GRB.OPTIMAL:
#         selected = [x.X.astype(int)[c, :].tolist().index(1) for c in C]
#         return selected
#     else:
#         m.write('model.mps')
#         m.setParam('OutputFlag', True)
#         m.optimize()
#         return None

def printProblem(votes, party_seats, NC, NP):
    print(f'Shape of constraint matrix: ({NC}, {NP})')
    nzp = np.array([[1 if votes[c, p] else 0 for p in range(NP)] for c in range(NC)])
    print(f'Votes:')
    print(votes)
    print(f'Nonzero pattern:')
    print(nzp)
    print('Max column sums (party_seats):')
    print(party_seats)
    print(f'Total seats: {np.sum(party_seats)}')

from pulp import *
def pulp_optimal_const(votes, party_seats):
    solvers = [GLPK_CMD, GUROBI, COIN_CMD]
    solver_to_use = 0;
    SOLVED = 1
    (NC, NP) = votes.shape
    P = range(NP)
    C = range(NC)
    m = LpProblem("PuLP_optimal_const", LpMaximize)
    A = np.log(np.where(votes > 0, votes, 1))
    x = {(c,p):LpVariable(f"x_{c}_{p}", cat=LpBinary) for p in P for c in C if votes[c,p]}
    obj = LpAffineExpression({x[c,p]: A[c,p] for p in P for c in C if votes[c,p]})
    csParty = [LpAffineExpression({x[c,p]: 1.0 for p in P if votes[c,p]}) for c in C]
    csConst = [LpAffineExpression({x[c,p]: 1.0 for c in C if votes[c,p]}) for p in P]
    m.setObjective(obj)
    for csp in csParty:
        m += LpConstraint(e=csp, sense=LpConstraintEQ, rhs=1.0)
    for csc, colsum in zip(csConst, party_seats):
        m += LpConstraint(csc, sense=LpConstraintLE, rhs = colsum)
    m.solve(solvers[solver_to_use](msg=0))
    if m.sol_status != SOLVED:
        status = m.sol_status
        print('*** Linear programming solver failure in single constituency alocation')
        printProblem(votes, party_seats, NC, NP)
        expl = constants.LpStatus[status] if status in constants.LpStatus else "unknown"
        raise RuntimeError(f"PuLP solver failed with status = {status} ({expl})")
    selected = np.zeros(NC, int)
    for c in C:
        for p in P:
            if votes[c,p] and x[c,p].value():
                selected[c] = p
    return selected
