#!/usr/bin/env python3
# - change-test
import numpy as np, pandas as pd, sys, json
from numpy import r_
from pathos.multiprocessing import ProcessingPool as Pool
sys.path.append('~/voting/backend')
sys.path.append('~/voting/backend/methods')
from readkerg import readkerg2021
from run_util import get_arguments, argument_string
from germany_dictionaries import all_land_methods, all_const_methods, method_funs_const, \
    method_funs_land, scalar_stats, land_stats, party_stats, by_land, by_party, \
    land_method_table, const_method_table
from germany_methods import apportion_sainte_lague
from division_rules import sainte_lague_gen
from running_stats import Running_stats, combine_stat
from util import disp, get_cpu_count, infeasible_error
from table_util import entropy_single, entropy
from result_tables import method_measure_table, measure_table
from calculate_seat_shares import calculate_seat_shares_orig
from randomize import random_votes, generate_votes, move_CDU_CSU
from datetime import datetime
import alternating_scaling

disp(width=60)
np.set_printoptions(suppress=True, floatmode="fixed", precision=3, linewidth=200)
ICORE = 0

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
        for s in land_stats['land']:  stat[s] = addrun(nland, f"{lm}-{s}")
        for s in party_stats:         stat[s] = addrun(nparty, s)
        for s in scalar_stats:        stat[s] = addrun(1, s)
    # for cm in constmethods:
    #     stats[cm] = {}
    #     stat = stats[cm]
    #     for s in land_stats['const']: stat[s] = addrun(nland, s)
    for method in pairmethods:
        stats[method] = {}
        stat = stats[method]
        for s in land_stats['pairs']: stat[s] = addrun(nland, f"{method}-{s}")
        #for s in scalar_stats:        stat[s] = addrun(1, s)
    return stats

def read_data():
    sæti_fylkja = pd.read_excel('sæti-fylkja.xlsx')
    land2sæti = dict(zip(sæti_fylkja.Land, sæti_fylkja.Sæti))
    with open('partyvotes.json') as f:
        data = json.load(f)
    data["nconst2021"] = [len(cv) for cv in data["cv"][-1]]
    data["landseats2021"] = [land2sæti[land] for land in data["lander"]]
    return data

def land_allocate(method, votes, partyseats, landseats):
    if method.endswith('C'):
        method = method[:-1]
    fun = method_funs_land[method]
    if method in {'party1st', 'land1st'}:
        alloc = fun(votes, partyseats, landseats)
    else:
        prior_alloc = np.zeros(votes.shape, int)
        alloc_seats, _ =  fun(votes, landseats, partyseats, prior_alloc, sainte_lague_gen)
        if alloc_seats is None:
            return None
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

def run_simulate(data, info, methodpairs, param, ntask, icore):
    alternating_scaling.icore = icore
    qm = info['quality-measures']
    uncorr = param['uncorr']
    seed = [icore, param['seed']] if param['seed'] else None
    # yr2021 = data['years'].index(2021)
    landseats = data["landseats2021"]
    # parties = data['parties'].copy()
    # länder = data["lander"]
    # PDS = parties.index('PDS')
    # partyvotes = np.delete(np.array(data["pv"][yr2021]), PDS, axis=1)
    # (nland, nparty) = partyvotes.shape
    # constvotes = [None]*nland
    # for l in range(nland):
    #     constvotes[l] = np.delete(np.array(data["cv"][yr2021][l]), PDS, axis=1)
    # parties.pop(PDS)
    # [constvotes, partyvotes] = move_CDU_CSU(constvotes, partyvotes, parties, länder)
    # nparty += 1
    # CDU = parties.index('CDU')
    # parties.insert(CDU + 1, 'CSU')
    nconst = data["nconst2021"]  #np.array([c.shape[0] for c in constvotes]);
    landmethods, constmethods, pairmethods = splitmethods(methodpairs)
    constmethod_dict = {lm: set() for lm in landmethods}
    rng = np.random.default_rng(seed)
    for p in pairmethods:
        (lm,cm) = p.split(':')
        constmethod_dict[lm].add(cm)
    # if uncorr:
    #     rsd = param['rsd']
    #     prsd = param['prsd']
    #     gcv, gpv = random_votes(ntask, partyvotes, prsd, constvotes, rsd, parties, rng)
    # else:
    gcv, gpv = generate_votes(ntask, nconst, rng, param)
    (nt, nland, nparty) = gpv.shape
    assert ntask == nt
    PARTY = 2
    share = [v/v.sum(PARTY)[:,:,None] for v in gcv]
    max_neg_marg = np.zeros(nland)
    neg_marg_count = np.zeros(nland)
    min_seat_share = np.zeros(nland)
    const_opt_diff = np.zeros(nland)
    winner_all_diff = np.zeros(nland)
    const_entropy = np.zeros(nland)
    stats = initialize_stats(methodpairs, nland, nparty)
    optimal_const_fun = method_funs_const["optimalC"]
    if qm == 'sel':
        pass
    for k in range(ntask):
        if icore==0 and k % 1 == 0:
            print(f'Simulation #{k} on core #{icore}')
        LAND = 0
        nat_vote_share = gpv[k].sum(axis=LAND)/gpv[k].sum()
        partyseats = r_[apportion_sainte_lague(nat_vote_share[:-1], 598), 0]
        seat_shares = calculate_seat_shares_orig(gpv[k], landseats, partyseats, 'both')
        selected_opt = {}
        entropy_opt = {}
        alloc = {}
        entro = {}
        for lm in landmethods:
            try:
                alloc[lm] = land_allocate(lm, gpv[k], partyseats, landseats)
            except infeasible_error:
                print('caught exception')
                raise
            entro[lm] = entropy(gpv[k], alloc[lm], sainte_lague_gen)
            selected_opt[lm] = {}
            entropy_opt[lm] = np.zeros(nland)
            for l in range(nland):
                voteshare = share[l][k]
                selected_opt[lm][l] = optimal_const_fun(voteshare, alloc[lm][l, :])
                entropy_opt[lm][l] = entropy_single(voteshare, selected_opt[lm][l])
        for lm in landmethods:
            party_alloc = alloc[lm].sum(axis=0)
            land_alloc = alloc[lm].sum(axis=1)
            party_disparity = party_alloc - partyseats
            land_disparity = land_alloc - landseats
            total_land_disparity = sum(np.maximum(land_disparity, 0))
            seats_minus_shares = abs(alloc[lm] - seat_shares).sum(0)
            entropy_diff = entro["optimal"] - entro[lm]
            #print('lm, ed:', lm, entropy_diff)
            opt_diff = abs(alloc[lm] - alloc["optimal"]).sum(0)
            stat = stats[lm]
            dispar = any(land_disparity) or any(party_disparity)
            failure_rate = 1 if dispar and not lm.endswith('1st') else 0
            stat['failure_rate'].update(failure_rate)
            stat['land_dispar'].update(land_disparity)
            stat['total_land_disparity'].update(total_land_disparity)
            stat['party_dispar'].update(party_disparity)
            stat['entropy_diff'].update(entropy_diff)
            stat['opt_diff'].update(opt_diff)
            stat['seats_minus_shares'].update(seats_minus_shares)
            stat['party_alloc'].update(party_alloc)
            stat['land_alloc'].update(land_alloc)
            for cm in constmethod_dict[lm]:
                const_method_fun = method_funs_const[cm]
                method = f"{lm}:{cm}"
                for l in range(nland):
                    voteshare = share[l][k]
                    if cm=="optimalC":
                        selected = selected_opt[lm][l]
                    else:
                        selected = const_method_fun(voteshare, alloc[lm][l, :])
                    I = range(nconst[l])
                    neg_margin = voteshare.max(axis=1) - voteshare[I, selected]
                    max_neg_marg[l] = neg_margin.max()
                    neg_marg_count[l] = np.sum(neg_margin > 0)
                    seat_share = voteshare[I, selected]
                    min_seat_share[l] = seat_share.min()
                    const_opt_diff[l] = seat_diff(selected_opt[lm][l], selected)
                    winner_all_diff[l] = sum(voteshare.argmax(axis=1) != selected)
                    const_entropy[l] = entropy_single(voteshare, selected)
                stat = stats[method]
                const_entropy_diff = entropy_opt[lm] - const_entropy
                stat['max_neg_marg'].update(max_neg_marg)
                stat['neg_marg_count'].update(neg_marg_count)
                stat['min_seat_share'].update(min_seat_share)
                stat['const_opt_diff'].update(const_opt_diff)
                stat['winner_all_diff'].update(winner_all_diff)
                stat['const_entropy_diff'].update(const_entropy_diff)
    return stats

def display_results(methodpairs, stats, data, info):
    (landmethods, constmethods, pairmethods) = splitmethods(methodpairs)
    # partyvotes = data["pv"]
    # data["partyseats"] = r_[apportion_sainte_lague(partyvotes.sum(0)[:-1], 598), 0]
    method_measure_table(landmethods, stats, info, 'land')
    method_measure_table(constmethods, stats, info, 'constituency')
    method_measure_table(pairmethods, stats, info, 'land-constituency')
    measure_table('optimal', stats, data, info, by_land, 'land')
    measure_table('party1st', stats, data, info, by_land, 'land')
    measure_table('absmarg', stats, data, info, by_land, 'land')
    measure_table('party1st:optimalC', stats, data, info, by_land, 'land')
    measure_table('party1st:relmargC', stats, data, info, by_land, 'land')
    measure_table('party1st:absmargC', stats, data, info, by_land, 'land')
    measure_table('party1st:votepctC', stats, data, info, by_land,  'land')
    measure_table('party1st:ampelC', stats, data, info, by_land,  'land')
    pass

def parallel_simulate(data, info, methods, param, ncores):
    nsim = param['nsim']
    ntask = [nsim//ncores + (1 if i < nsim % ncores else 0) for i in range(ncores)]
    pool = Pool(ncores)
    icores = list(range(ncores))
    stats = pool.map(run_simulate, [data]*ncores, [info]*ncores, [methods]*ncores,
                     [param]*ncores, ntask, icores)
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
        constmethods = remove_duplicates([pair[1] for pair in methodlist if pair[1]])
        pairmethods = [f"{pair[0]}:{pair[1]}" for pair in methodlist if pair[1]]
    else:
        landmethods = methodlist
        constmethods = []
        pairmethods = []
    if 'optimal' not in landmethods:
        landmethods.append('optimal')
    return landmethods, constmethods, pairmethods

def save_stats(stats):
    import os, json, gzip
    env = os.environ
    if "SLURM_ARRAY_JOB_ID" in env:
        jobid = env["SLURM_ARRAY_JOB_ID"] + ":" + env["SLURM_ARRAY_TASK_ID"]
    else:
        jobid = os.environ.get("SLURM_JOB_ID", os.getpid())
    file = f"stats-{jobid}.gz"
    D = Running_stats.to_dicts(stats)
    with gzip.open(file, "wt") as f:
        json.dump(D, f)
    return jobid

def load_stats(file):
    import json, gzip
    with gzip.open(file) as f:
        D = json.load(f)
    return Running_stats.from_dicts(D)

def main():
    # NÁ Í SKIPANALÍNUVIÐFÖNG
    pairs = []
    pairs.extend([
        ('relsupmed', ''),
        ('relsup', ''),
        # ('switch', ''),
        ('votepct', ''),
        ('absmarg', ''),
        ('relmarg', ''),
        ('optimal', 'optimalC'),
        ('optimal', 'relmargC'),
        ('optimal', 'absmargC'),
        ('optimal', 'votepctC'),
        ('optimal', 'ampelC'),
        ('party1st', 'optimalC'),
        ('party1st', 'relmargC'),
        ('party1st', 'absmargC'),
        ('party1st', 'votepctC'),
        ('party1st', 'ampelC'),
    ])
    all = [(m1, m2) for m1 in all_land_methods for m2 in all_const_methods]
    method_desc =('methods [pairs, all or mland+...:mconst+...,... where mland is one of:'
                   + land_method_table + '\n'
                   + 'and mconst is one of:'
                   + const_method_table + '\n]')
    uncorr_desc = 'use uncorrelated votes with RSD given by options -c & -p'
    args = [
        ['nsim',    int, ('total number of simulations\n' +
                          '(if 0, combine stats-files given on command line:\n' +
                          '   run.py 0 [options] stats_xxx.gz...)'), 100],
        ['-detail', bool, 'show results with CI and SD'],
        ['-uncorr', bool, uncorr_desc],
        ['-ncores', int,  'number of cores (0 to use all available)', 0, 'N'],
        ['-seed',   int,  'seed to use', None],
        ['-methods',str,  method_desc, 'pairs'],
        ['-qm',     str,  'quality measures [all/sel]', 'sel'],
        ['-Quiet',  bool, 'suppress output'],
        ['-rsd',    float,'relative SD for constituency vote generation',  0.3],
        ['-prsd',   float,'relative SD for party vote generation', 0.1],
    ]
    desc = "Simulate for the whole of Germany using correlated votes by default"

    (nsim, detail, uncorr, ncores, seed, methods, qm, Quiet, rsd, prsd, combine) = \
                                                get_arguments(args=args, description=desc)

    if ncores==0:
        ncores = get_cpu_count()
    print(f'cpu_count={get_cpu_count()}')
    ncores = min(ncores, nsim)

    if methods=='all':
        method_list = all
    elif methods=='pairs':
        method_list = pairs
    else:
        method_list = []
        mpairs = methods.split(',')
        for mp in mpairs:
            (lmethods, cmethods) = mp.split(':')
            lms = lmethods.split('+')
            cms = cmethods.split('+')
            for lm in lms:
                for cm in cms:
                    method_list.append((lm, cm + 'C' if cm else cm))
    info, _ = readkerg2021()
    SSW = list(info["party"].values()).index('SSW')
    del info["party"][SSW]
    info['detail'] = detail
    info['quality-measures'] = qm
    data = read_data()
    # RUN THE SIMULATION
    print(f'Time:    {datetime.now().strftime("%d-%b-%Y %H:%M")}')
    print(f'Options: {argument_string()}')
    if nsim > 0:
        percore = round(nsim/ncores, 1)
        print(f'Carrying out {nsim} simulations on {ncores} cores ({percore} per core)')
        param = {'rsd':rsd, 'prsd':prsd, 'nsim':nsim, 'uncorr':uncorr, 'seed':seed}
        if ncores == 1:
            stats = run_simulate(data, info, method_list, param, nsim, 0)
        else:
            stats = parallel_simulate(data, info, method_list, param, ncores)
        jobid = save_stats(stats)
    else:
        print(f'Combining results from several nodes')
        assert(len(combine) > 0)
        stats = load_stats(combine[0])
        for f in combine[1:]:
            print(f'File: {f}')
            s = load_stats(f)
            combine_stat(stats, s)
    if not Quiet:
        display_results(method_list, stats, data, info)
    else:
        jobid = save_stats(stats)
        print(f'Saving statistics for job {jobid}')

if __name__ == "__main__":
    main()

