#!/usr/bin/env python3
# - change-test
import numpy as np
from numpy import r_
import sys
ICORE = 0
from pathos.multiprocessing import ProcessingPool as Pool
sys.path.append('~/voting/backend')
sys.path.append('~/voting/backend/methods')
np.set_printoptions(suppress=True, floatmode="fixed", precision=3, linewidth=200)
from readkerg import readkerg
from run_util import get_arguments
from dictionaries import all_land_methods, all_const_methods, method_funs_const, \
    method_funs_land, scalar_stats, land_stats, party_stats, by_land, by_party, \
    matrix_stats
from germany_methods import apportion_sainte_lague
from division_rules import sainte_lague_gen
from running_stats import Running_stats, combine_stat
from util import disp
from table_util import entropy_single, entropy
from result_tables import method_measure_table, measure_table
from calculate_seat_shares import calculate_seat_shares
import alternating_scaling
disp(width=60)

# from time import sleep

def calc_share(votes):
    share = [v/np.sum(v,1)[:,None] for v in votes]
    return share

def randomize_votes(votes, partyvotes, cv, pcv, nsim):
    rng = np.random.default_rng(68)
    shape = 1/cv**2
    scale = 1/shape
    gv = []
    for i in range(len(votes)):
        size = (nsim,) + np.shape(votes[i])
        randvotes = rng.gamma(shape, scale, size=size)*votes[i]
        #randvotes = np.rint(randvotes).astype(int)
        gv.append(randvotes)
    shapep = 1/pcv**2
    scalep = 1/shapep
    sizep = (nsim,) + np.shape(partyvotes)
    gpv = rng.gamma(shapep, scalep, size = sizep)*partyvotes
    #gpv = np.rint(gpv).astype(int) # don't use this for percentages
    return gv, gpv

def addrun(n, name):
    r = Running_stats(
        shape = n,
        name = name,
        options = None if n == 1 else 'all')
    return r

def initialize_stats(methodlist, nland, nparty):
    stats = {}
    landmethods, constmethods, pairmethods = splitmethods(methodlist)
    for lm in landmethods:
        stats[lm] = {}
        stat = stats[lm]
        for s in land_stats['land']:  stat[s] = addrun(nland, f"{lm}:{s}")
        for s in party_stats:         stat[s] = addrun(nparty + 1, s)
        for s in matrix_stats:        stat[s] = addrun((nland, nparty + 1), s)
        for s in scalar_stats:        stat[s] = addrun(1, s)
    for cm in constmethods:
        stats[cm] = {}
        stat = stats[cm]
        for s in land_stats['const']: stat[s] = addrun(nland, s)
    for method in pairmethods:
        stats[method] = {}
        stat = stats[method]
        for s in land_stats['pairs']: stat[s] = addrun(nland, f"{method}:{s}")
        #for s in scalar_stats:        stat[s] = addrun(1, s)
    return stats

def land_allocate(method, votes, partyseats, landseats):
    if method.endswith('C'):
        method = method[:-1]
    fun = method_funs_land[method]
    if method in {'party1st', 'land1st'}:
        alloc = fun(votes, partyseats, landseats)
    elif method == 'optimal':
        prior_alloc = np.zeros(votes.shape, int)
        alloc_seats, _ =  fun(votes, landseats, partyseats, prior_alloc, sainte_lague_gen)
        alloc = np.array(alloc_seats)
    else:
        prior_alloc = np.zeros(votes.shape, int)
        alloc_seats, _ =  fun(votes, landseats, partyseats, prior_alloc, sainte_lague_gen)
        alloc = np.array(alloc_seats)
    return alloc

def seat_diff(selected1, selected2):
    d = sum(s1 != s2 for (s1, s2) in zip(selected1, selected2))
    return d

def entropy_matrix(votes, seats, divisor_gen):
    div_gen = divisor_gen()
    div = np.array([next(div_gen) for _ in range(seats.max())])
    (m,n) = votes.shape
    L = range(m)
    P = range(n)
    entropy = np.zeros((m,n))
    for l in L:
        for p in P:
            if votes[l,p] > 0:
                for s in range(seats[l,p]):
                    entropy[l,p] += np.log(votes[l,p]/div[s])
    return entropy

def run_simulate(data, methodpairs, param, ntask, icore):
    alternating_scaling.icore = icore
    landseats = data["landseats"]
    partyvotes = data["partyvotes"]
    constvotes = data["constvotes"]
    (nland, nparty) = partyvotes.shape
    landmethods, constmethods, pairmethods = splitmethods(methodpairs)
    constmethod_dict = {lm: set() for lm in landmethods}
    for p in pairmethods:
        (lm,cm) = p.split('-')
        constmethod_dict[lm].add(cm)
    nparty -= 1
    nconst = [len(v) for v in constvotes]
    cv = param['cv']
    pcv = param['pcv']
    gv, gpv = randomize_votes(constvotes, partyvotes, cv, pcv, ntask)
    share = [calc_share(v) for v in gv]
    max_neg_marg = np.zeros(nland)
    neg_marg_count = np.zeros(nland)
    min_seat_share = np.zeros(nland)
    opt_opt_diff = np.zeros(nland)
    stats = initialize_stats(methodpairs, nland, nparty)
    optimal_const_fun = method_funs_const["optimalC"]
    const_opt_diff = np.zeros(nland)
    const_entropy = np.zeros(nland)
    for k in range(ntask):
        if icore==0 and k % 1 == 0:
            print(f'Simulation #{k} on core #{icore}')
        nat_vote_share = gpv[k].sum(axis=0)/gpv[k].sum()
        partyseats = r_[apportion_sainte_lague(nat_vote_share[:-1], 598), 0]
        seat_shares = calculate_seat_shares(gpv[k], landseats, partyseats, 'both')
        opt_alloc = land_allocate("gurobi", gpv[k], partyseats, landseats)
        opt_entropy = entropy(gpv[k], opt_alloc, sainte_lague_gen)
        selected_opt_opt = {}
        selected_opt = {}
        entropy_opt_opt = np.zeros(nland)
        for l in range(nland):
            selected_opt_opt[l] = optimal_const_fun(gv[l][k], opt_alloc[l, :])
            entropy_opt_opt[l] = entropy_single(gv[l][k], selected_opt_opt[l])
        for cm in constmethods:
            selected_opt[cm] = {}
            cm_fun = method_funs_const[cm]
            for l in range(nland):
                selected_opt[cm][l] = cm_fun(gv[l][k], opt_alloc[l, :])
                const_opt_diff[l] = seat_diff(selected_opt_opt[l], selected_opt[cm][l])
                const_entropy[l] = entropy_single(gv[l][k], selected_opt[cm][l])
            const_entropy_diff = entropy_opt_opt - const_entropy
            stat = stats[cm]
            stat['const_opt_diff'].update(const_opt_diff)
            if sum(const_opt_diff) > 0 and cm == "relmargC":
                pass
            stat['const_entropy_diff'].update(const_entropy_diff)
        for lm in landmethods:
            if lm == "optimal":
                alloc = land_allocate(lm, gpv[k], partyseats, landseats)
                #alloc = opt_alloc
            else:
                alloc = land_allocate(lm, gpv[k], partyseats, landseats)
            party_alloc = alloc.sum(axis=0)
            land_alloc = alloc.sum(axis=1)
            party_disparity = party_alloc - partyseats
            land_disparity = land_alloc - landseats
            total_land_disparity = sum(np.maximum(land_disparity, 0))
            seats_minus_shares = abs(alloc - seat_shares)
            entropy_diff = opt_entropy - entropy(gpv[k], alloc, sainte_lague_gen)
            opt_diff = abs(alloc - opt_alloc)
            stat = stats[lm]
            dispar = any(land_disparity) or any(party_disparity)
            failure_rate = 1 if dispar and not lm.endswith('1st') else 0
            stat['failure_rate'].update(failure_rate)
            #print('failure_rate=', failure_rate)
            stat['land_dispar'].update(land_disparity)
            stat['total_land_disparity'].update(total_land_disparity)
            stat['party_dispar'].update(party_disparity)
            if not dispar or lm.endswith('1st'):
                stat['entropy_diff'].update(entropy_diff)
            stat['opt_diff'].update(opt_diff)
            stat['seats_minus_shares'].update(seats_minus_shares)
            stat['party_alloc'].update(party_alloc)
            stat['land_alloc'].update(land_alloc)
            for cm in constmethod_dict[lm]:
                const_method_fun = method_funs_const[cm]
                method = f"{lm}-{cm}"
                for l in range(nland):
                    voteshare = share[l][k]
                    if lm=="optimal":
                        selected = selected_opt[cm][l]
                    else:
                        selected = const_method_fun(voteshare, alloc[l, :])
                    I = range(nconst[l])
                    neg_margin = voteshare[:, :-1].max(axis=1) - voteshare[I, selected]
                    max_neg_marg[l] = neg_margin.max()
                    neg_marg_count[l] = np.sum(neg_margin > 0)
                    seat_share = voteshare[I, selected]
                    min_seat_share[l] = seat_share.min()
                    opt_opt_diff[l] = seat_diff(selected_opt_opt[l], selected)
                stat = stats[method]
                stat['max_neg_marg'].update(max_neg_marg)
                stat['neg_marg_count'].update(neg_marg_count)
                stat['min_seat_share'].update(min_seat_share)
                stat['opt_opt_diff'].update(opt_opt_diff)
    return stats

def display_results(methodpairs, stats, data, info):
    (landmethods, constmethods, pairmethods) = splitmethods(methodpairs)
    partyvotes = data["partyvotes"]
    data["partyseats"] = r_[apportion_sainte_lague(partyvotes.sum(0)[:-1], 598), 0]
    method_measure_table(landmethods, stats, 'land')
    method_measure_table(constmethods, stats, 'constituency')
    method_measure_table(pairmethods, stats, 'land-constituency')
    measure_table('optimal', stats, data, info, by_land, 'land')
    measure_table('absmarg', stats, data, info, by_land, 'land')
    measure_table('party1st', stats, data, info, by_land, 'land')
    measure_table('land1st', stats, data, info, by_party, 'party')
    measure_table('relmarg-relmargC', stats, data, info, by_land, 'land')
    measure_table('optimal-optimalC', stats, data, info, by_land, 'land')
    measure_table('party1st-votepctC', stats, data, info, by_land,  'land')
    measure_table('party1st-votepctC', stats, data, info, by_party, 'party')
    # lvp = measure_table(stats, data, 'votepct-party1st', 'land')
    # for df in (mm_table, lvv, lrr, pvp, pvl, lvp, loo):
    #     print_df(df, wrap_headers=True)
    pass

def parallel_simulate(data, methods, param, ncores):
    nsim = param['nsim']
    ntask = [nsim//ncores + (1 if i < nsim % ncores else 0) for i in range(ncores)]
    pool = Pool(ncores)
    icores = list(range(ncores))
    stats = pool.map(run_simulate, [data]*ncores, [methods]*ncores, [param]*ncores, ntask,
                     icores)
    running0 = stats.pop(0)
    for r in stats:
        combine_stat(running0, r)
    return running0

def remove_duplicates(L):
    newL = []
    for l in L:
        if l not in newL:
            newL.append(l)
    return newL

def splitmethods(methodlist):
    if isinstance(methodlist[0], (tuple, list)):
        landmethods = remove_duplicates([pair[0] for pair in methodlist])
        constmethods = remove_duplicates([pair[1]+'C' for pair in methodlist if pair[1]])
        pairmethods = [f"{pair[0]}-{pair[1] + 'C'}" for pair in methodlist if pair[1]]
    else:
        landmethods = methodlist
        constmethods = []
        pairmethods = []
    return landmethods, constmethods, pairmethods

def main():
    # NÁ Í SKIPANALÍNUVIÐFÖNG
    pairs = []
    pairs.extend([
        ('optimal', 'optimal'),
        ('optimal', 'relmarg'),
        ('optimal', 'absmarg'),
        ('optimal', 'votepct'),
        ('relmarg', ''),
        ('absmarg', ''),
        ('switch', ''),
        ('relsup', ''),
        ('party1st', 'votepct'),
        ('votepct', 'scand'),
        ('land1st', 'votepct'),
        ('votepct', 'votepct'),
    ])
    all = [(m1, m2) for m1 in all_land_methods for m2 in all_const_methods]
    method_desc = '[pairs, all, or m1-m2 (e.g. scand-votepct]'
    args = [
        ['nsim', int, 'total number of simulations', 5],
        ['-ncores', int, 'number of cores', 8],
        ['-methods', str, f'methods {method_desc}', 'pairs'],
        ['-cv', float, 'variation coefficient for constituency vote generation',  0.3],
        ['-pcv', float, 'variation coefficient for party vote generation', 0.1]]
    desc = "Simulate for the whole of Germany"
    (nsim, ncores, methods, cv, pcv) = get_arguments(args=args, description=desc)
    ncores = min(ncores, nsim)
    if methods=='all':     methods = all
    elif methods=='pairs': methods = pairs
    elif '-' in methods:   methods = [methods.split('-')]
    else:                  methods = methods.split(',')

    info, data = readkerg()

    # RUN THE SIMULATION
    percore = round(nsim/ncores, 1)
    print(f'Carrying out {nsim} simulations on {ncores} cores ({percore} per core)')
    param = {'cv':cv, 'pcv':pcv, 'nsim':nsim}
    if ncores == 1:
        stats = run_simulate(data, methods, param, nsim, 0)
    else:
        stats = parallel_simulate(data, methods, param, ncores)
    display_results(methods, stats, data, info)

if __name__ == "__main__":
    main()
