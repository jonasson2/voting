#!/usr/bin/env python3
# - change-test
import numpy as np
from numpy import c_, r_
import sys
from pathos.multiprocessing import ProcessingPool as Pool
sys.path.append('~/voting/backend')
sys.path.append('~/voting/backend/methods')
np.set_printoptions(suppress=True, floatmode="fixed", precision=3, linewidth=200)
from readkerg import readkerg
from run_util import get_arguments
from dictionaries import all_land_methods, all_const_methods, party_measures, \
    land_measures, land_abbrev, const_method_funs, land_method_funs
from methods import apportion_sainte_lague
from division_rules import sainte_lague_gen
from running_stats import Running_stats, combine_stat
from util import disp
from result_tables import method_measure_table, measure_table, print_df
disp(width=60)
from time import sleep

def calc_share(votes):
    share = [v/np.sum(v,1)[:,None] for v in votes]
    return share

def randomize_votes(votes, partyvotes, cv, cvp, nsim):
    rng = np.random.default_rng(seed=45)
    shape = 1/cv**2
    scale = 1/shape
    gv = []
    for i in range(len(votes)):
        size = (nsim,) + np.shape(votes[i])
        randvotes = rng.gamma(shape, scale, size=size)*votes[i]
        #randvotes = np.rint(randvotes).astype(int)
        gv.append(randvotes)
    shapep = 1/cvp**2
    scalep = 1/shapep
    sizep = (nsim,) + np.shape(partyvotes)
    gpv = rng.gamma(shapep, scalep, size = sizep)*partyvotes
    #gpv = np.rint(gpv).astype(int) # don't use this for percentages
    return gv, gpv

def initialize_running(const_meth, land_meth, nland, nparty, parties, länder):
    running = {}
    for cm in const_meth:
        for lm in land_meth:
            method = f'{cm}-{lm}'
            running[method] = {}
            for measure in party_measures:
                running[method][measure] = Running_stats (
                    shape = nparty + 1,
                    name = f"{method}-{measure}",
                    entries = parties,
                    options = ['mean', 'max', 'min', 'sum'])
            for measure in land_measures:
                running[method][measure] = Running_stats(
                    shape = nland,
                    name = f"{method}-{measure}",
                    entries = länder,
                    options = ['mean', 'sum', 'min', 'max'])
    return running

def land_allocate(method, votes, partyseats, landseats):
    fun = land_method_funs[method]
    if method in {'party1st', 'land1st'}:
        alloc = fun(votes, partyseats, landseats)
    elif method == 'optimal':
        prior_alloc = np.zeros(votes.shape, int)
        alloc_seats, _ =  fun(votes, landseats, partyseats, prior_alloc, sainte_lague_gen,
                              False, [0], 0)
        alloc = np.array(alloc_seats)
    else:
        prior_alloc = np.zeros(votes.shape, int)
        alloc_seats, _ =  fun(votes, landseats, partyseats, prior_alloc, sainte_lague_gen)
        alloc = np.array(alloc_seats)
    return alloc

def run_simulate(info, data, const_methods, land_methods, nsim, icore):
    landseats = data["landseats"]
    partyvotes = data["partyvotes"]
    constvotes = data["constvotes"]
    (nland, nparty) = partyvotes.shape
    nparty -= 1
    nconst = [len(v) for v in constvotes]
    gv, gpv = randomize_votes(constvotes, partyvotes, cv, pcv, nsim)
    share = [calc_share(v) for v in gv]
    max_neg_marg = np.zeros(nland)
    neg_marg_count = np.zeros(nland)
    min_seat_share = np.zeros(nland)
    parties = list(info["party"].values())
    #länder = list(info["land"].values())
    länder = list(land_abbrev.values())
    running = initialize_running(const_methods, land_methods, nland,nparty,parties,länder)
    ref_alloc = None
    for k in range(nsim):
        if icore==0 and k % 10 == 0:
            print(f'Simulation #{k} on core #{icore}')
        for const_method in const_methods:
            const_method_fun = const_method_funs[const_method]
            nat_vote_share = gpv[k].sum(axis=0)/gpv[k].sum()
            partyseats = apportion_sainte_lague(nat_vote_share[:-1], 598)
            partyseats = r_[partyseats, 0]
            for land_method in land_methods:
                alloc = land_allocate(land_method, gpv[k], partyseats, landseats)
                if k==0 and icore==0: # First simulation and first processor
                    ref_alloc = land_allocate(land_method,partyvotes,partyseats,landseats)
                party_alloc = alloc.sum(axis=0)
                land_alloc = alloc.sum(axis=1)
                party_disparity = party_alloc - partyseats
                land_disparity = land_alloc - landseats
                method = f"{const_method}-{land_method}"
                for l in range(nland):
                    voteshare = share[l][k]
                    selected = const_method_fun(voteshare, alloc[l, :])
                    I = range(nconst[l])
                    neg_margin = voteshare[:,:-1].max(axis=1) - voteshare[I, selected]
                    max_neg_marg[l] = neg_margin.max()
                    neg_marg_count[l] = np.sum(neg_margin > 0)
                    seat_share = voteshare[I, selected]
                    min_seat_share[l] = seat_share.min()
                runmeth = running[method]
                runmeth['party_alloc'].update(party_alloc)
                runmeth['land_alloc'].update(land_alloc)
                runmeth['max_neg_marg'].update(max_neg_marg)
                runmeth['min_seat_share'].update(min_seat_share)
                runmeth['min_land_dispar'].update(land_disparity)
                runmeth['max_land_dispar'].update(land_disparity)
                runmeth['min_party_dispar'].update(party_disparity)
                runmeth['max_party_dispar'].update(party_disparity)
                runmeth['neg_marg_count'].update(neg_marg_count)

    return running, ref_alloc

def display_results(running, data, ref_alloc):
    nconst = [len(v) for v in data["constvotes"]]
    mm_table = method_measure_table(running)
    lvv = measure_table(running, ref_alloc, 'votepct-votepct', 'land')
    lrr = measure_table(running, ref_alloc, 'relmarg-relmarg', 'land')
    loo = measure_table(running, ref_alloc, 'optimal-optimal', 'land')
    pvp = measure_table(running, ref_alloc, 'votepct-party1st', 'party')
    pvl = measure_table(running, ref_alloc, 'votepct-land1st', 'party')
    lvp = measure_table(running, ref_alloc, 'votepct-party1st', 'land')
    for df in (mm_table, lvv, lrr, pvp, pvl, lvp, loo):
        print_df(df, wrap_headers=True)
    pass

def parallel_simulate(info, data, const_methods, land_methods, nsim, ncores):
    ntask = [nsim//ncores + (1 if i < nsim % ncores else 0) for i in range(ncores)]
    pool = Pool(ncores)
    icores = list(range(ncores))
    results = pool.map(run_simulate, [info]*ncores, [data]*ncores, [const_methods]*ncores,
                       [land_methods]*ncores, ntask, icores)
    running = [r[0] for r in results]
    ref_alloc = results[0][1]
    running0 = running.pop(0)
    for r in running:
        combine_stat(running0, r)
    return running0, ref_alloc

if __name__ == "__main__":

    # NÁ Í SKIPANALÍNUVIÐFÖNG
    pm_list = '/'.join(all_land_methods) + '/all'
    cm_list = '/'.join(all_const_methods) + '/all'
    args = [
       ['nsim', int, 'total number of simulations', 5],
       ['-ncores', int, 'number of cores', 8],
       ['-erstmethod', str, f'method for constituency votes [{cm_list} or all]', 'all'],
       ['-zweitmethod', str, f'method for party votes [{pm_list} or all]', 'all'],
       ['-cv', float, 'variation coefficient for constituency vote generation',  0.3],
       ['-pcv', float, 'variation coefficient for party vote generation', 0.1]]
    desc = "Simulate for the whole of Germany"
    (nsim, ncores, erst, zweit, cv, pcv) = get_arguments(args=args, description=desc)
    ncores = min(ncores, nsim)
    const_methods = all_const_methods if erst == 'all' else erst.split(',')
    land_methods = all_land_methods if zweit == 'all' else zweit.split(',')

    info, data = readkerg()

    # RUN THE SIMULATION
    percore = round(nsim/ncores, 1)
    print(f'Carrying out {nsim} simulations on {ncores} cores ({percore} per core)')
    if ncores == 1:
        running, ref_alloc = run_simulate(info, data, const_methods,land_methods,nsim,0)
    else:
        running, ref_alloc = parallel_simulate(info, data, const_methods, land_methods,
                                               nsim, ncores)
    display_results(running, data, ref_alloc)
