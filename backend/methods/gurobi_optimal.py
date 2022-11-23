import numpy as np

def gurobi_optimal(m_votes,
           v_desired_row_sums,
           v_desired_col_sums,
           m_prior_allocations,
           divisor_gen,
           nat_prior_allocations=None,
           **kwargs):
    votes = np.array(m_votes)
    const_seats = np.array(v_desired_row_sums, int)
    (nrows, ncols) = np.shape(votes)
    prior_alloc = np.array(m_prior_allocations, int)
    nat_prior_alloc = (np.zeros(ncols, int) if nat_prior_allocations is None
                       else np.array(nat_prior_allocations, int))
    party_seats = np.array(v_desired_col_sums) - nat_prior_alloc
    div_gen = divisor_gen()
    N = max(max(const_seats), max(party_seats)) + 1
    div = np.array([next(div_gen) for _ in range(N + 1)])
    x = gurobi_max(votes, const_seats, party_seats, div, prior_alloc)
    stepbystep = {"data": [], "function": print_demo_table}
    return x.astype(int), stepbystep

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
    m.addConstrs((sum(n[c,:]) == const_seat_sum[c] for c in C))
    obj = gp.LinExpr()
    for c in C:
        s0 = prior_const_seats[c]
        for s in S[c]:
            a = np.log(np.where(votes[c,:] > 0, votes[c,:]/div[s], 1))
            obj.add(gp.LinExpr((a[p], x[c][p,s-s0]) for p in P))
    m.setObjective(obj, sense=gp.GRB.MAXIMIZE)
    m.setParam('OutputFlag', False)
    m.optimize()
    n = n.X.astype(int)
    return n + prior_alloc

def print_demo_table(rules, allocation_sequence):
    return [], [], None
