from run_util import get_arguments
from noweb import load_json
from os.path import splitext as splittext
import sys
sys.path.append('~/voting/allt-thyskaland')
from germany_methods import apportion_sainte_lague

def read_excel(file):
    import pandas as pd, numpy as np
    np.set_printoptions(linewidth=140)
    df = pd.read_excel(file, index_col=0)
    votes = np.array(df.iloc[:-1, :-1])
    const_seats = np.array(df.Total[:-1]).astype(int).tolist()
    party_seats = np.array(df.loc["Total"][:-1]).astype(int).tolist()
    #display(df)
    return (votes, const_seats, party_seats)

def read_json(filename):
    jsondata = load_json(filename)
    if "vote_table" in jsondata:
        vote_table = jsondata["vote_table"]
        votes = vote_table["votes"]
        const_seats = [c['num_adj_seats'] + c['num_fixed_seats']
                       for c in vote_table['constituencies']]
        party_vote_info = vote_table['party_vote_info']
        if party_vote_info['specified']:
            nat_votes = party_vote_info['votes']
            total_seats = (party_vote_info['num_fixed_seats'] +
                           party_vote_info['num_adj_seats'] +
                           sum(const_seats))
        else:
            nat_votes = [sum(v) for v in zip(*votes)]
            total_seats = sum(const_seats)
        party_seats = apportion_sainte_lague(nat_votes, total_seats)
    else:
        raise ValueError('No vote table found in json file')
        pass
    return votes, const_seats, party_seats

def read_data(filename):
    (root, ext) = splittext(filename)
    if ext=='.xlsx':
        (votes, const_seats, party_seats) = read_excel(filename)
    elif ext=='.json':
        (votes, const_seats, party_seats) = read_json(filename)
    else:
        raise ValueError('File extension must be .xlsx or .json')
    return (np.array(votes), const_seats, party_seats)

def gurobi_objval(model, vars, values):
    model.update()
    m = model.copy()
    for var,val in zip(vars, values):
        model.addConstrs((var == val))
    model.optimize()

import numpy as np
def gurobi_max(votes, const_seats, party_seats, div, prior_alloc=None, start=None):
    import gurobipy as gp
    (NC, NP) = votes.shape
    if prior_alloc is None:
        prior_alloc = np.zeros(votes.shape)
    P = range(NP)
    C = range(NC)
    prior_const_seats = prior_alloc.sum(1)
    prior_party_seats = prior_alloc.sum(0)
    party_bound = party_seats - prior_party_seats
    const_seat_sum = const_seats - prior_const_seats
    x_count = [const_seats[c] - int(prior_const_seats[c]) for c in C]
    S = [range(prior_const_seats[c], const_seats[c]) for c in C]
    m = gp.Model()
    x = []
    for c in C:
        var = m.addMVar((NP, int(x_count[c])), vtype='B')
        x.append(var)
    n = m.addMVar(votes.shape, vtype=gp.GRB.INTEGER)
    if start is not None:
        n.start = start
        for c in C:
            s0 = prior_const_seats[c]
            for s in S[c]:
                x[c][:,s-s0].start = [int(s < start[c,p]) for p in P]
    m.addConstrs((n[c,p] == sum(x[c][p,:]) for c in C for p in P))
    m.addConstrs((sum(n[:,p]) <= party_bound[p] for p in P))
    # m.addConstrs((n[c,:] >= prior_alloc[c,:] for c in C))
    m.addConstrs((sum(n[c,:]) == const_seat_sum[c] for c in C))
    obj = gp.LinExpr()
    for c in C:
        s0 = prior_const_seats[c]
        for s in S[c]:
            #print(c,s)
            a = np.log(np.maximum(1,votes[c,:])/div[s])
            obj.add(gp.LinExpr((a[p], x[c][p,s-s0]) for p in P))
    m.setObjective(obj, sense=gp.GRB.MAXIMIZE)

    m.setParam('OutputFlag', False)
    # m.setParam('MIPGap', 1e-10)
    # m.setParam('MipGapAbs', 1e-10)
    # m.setParam('Presolve', 2)
    # m.setParam('IntFeasTol', 1e-8)
    # m.setParam('OptimalityTol', 1e-8)
    m.optimize()
    prior_entropy = entropy(votes, prior_alloc, div)
    print('prior_entropy:', prior_entropy)
    print('optimal value:', m.objVal)
    print('sum:', prior_entropy + m.objVal)
    v = m.getVars
    n = n.X.astype(int)
    return n + prior_alloc

def entropy(votes, seats, div):
    (m,n) = votes.shape
    C = range(m)
    P = range(n)
    summa = 0
    for c in C:
        for p in P:
            for s in range(seats[c,p]):
                summa += np.log(np.maximum(1, votes[c,p])/div[s])
    return summa

import sys
sys.path.append('/Users/jonasson/voting/backend')
sys.path.append('/Users/jonasson/voting/backend/methods')
from alternating_scaling import alt_scaling
from division_rules import sainte_lague_gen

def optimal(votes, const_seats, party_seats, prior_alloc):
    seats, _ = alt_scaling(votes, const_seats, party_seats, prior_alloc, sainte_lague_gen)
    return np.array(seats)

def half_alloc(votes, const_seats, party_seats):
    # Allocate 2/3 of the seats, and make sure the result is within bounds
    from numpy import flatnonzero as find
    alloc = np.zeros(votes.shape, int)
    (nconst, nparty) = votes.shape
    for i in range(nconst):
        alloc[i,:] = apportion_sainte_lague(votes[i], const_seats[i])/10
    for j in range(nparty):
        while sum(alloc[:,j]) > party_seats[j]:
            k = find(alloc[:,j])[0]
            alloc[k,j] -= 1
    return alloc

def prufa():
    (filename,) = get_arguments(
        args=[
            ('file', str, 'excel file with votes', '~/dropbox/voting/germany-2021.xlsx')
        ],
        description="Comapare alternating scaling and Gurobi for optimal method")
    (votes, const_seats, party_seats) = read_data(filename)

    zero_seats = np.zeros(votes.shape, int)
    SL_div = np.arange(1, 2*max(party_seats) + 1, 2)
    for has_prior_alloc in [True]:
        print('\nWITH FIXED SEATS:' if has_prior_alloc else 'ALL SEATS ADJUSTMENT SEATS:')
        prior_alloc = (half_alloc(votes, const_seats, party_seats) if has_prior_alloc
                       else zero_seats)
        altscal_seats = optimal(votes, const_seats, party_seats, prior_alloc)
        start = altscal_seats - prior_alloc
        lp_seats = gurobi_max(votes, const_seats, party_seats, SL_div, prior_alloc, start)
        print(f'seat difference: {np.sum(np.abs(lp_seats - altscal_seats))}')
        print('Entropy:')
        print(f'  {entropy(votes, altscal_seats, SL_div)}')
        print(f'  {entropy(votes, lp_seats, SL_div)}')
        if sum(party_seats) == sum(const_seats):
            print('With land seats halved:')
            half_seats = [l//2 for l in const_seats]
            prior_alloc = (half_alloc(votes, half_seats, party_seats) if has_prior_alloc
                           else zero_seats)
            lp_half_seats = gurobi_max(votes, half_seats, party_seats, SL_div,prior_alloc)
            altscal_half_seats = optimal(votes, half_seats, party_seats, prior_alloc)
            print(f'seat difference: {sum(np.abs(lp_half_seats - altscal_half_seats))}')
            print(f'  {entropy(votes, altscal_half_seats, SL_div)}')
            print(f'  {entropy(votes, lp_half_seats, SL_div)}')

prufa()
