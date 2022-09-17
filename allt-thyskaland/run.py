#!/usr/bin/env python3
# - change-test
import numpy as np, pandas as pd
from numpy import c_, r_
import sys
from pathos.multiprocessing import ProcessingPool as Pool
import multiprocessing as mp
sys.path.append('~/voting/backend')
sys.path.append('~/voting/backend/methods')
np.set_printoptions(suppress=True, floatmode="fixed", precision=3, linewidth=200)
from readkerg import readkerg
from run_util import get_arguments
from dictionaries import land_method_dicts, const_method_dicts, all_land_methods, \
    all_const_methods, party_measures, \
    land_measures, land_abbrev, measure_formats, const_method_funs, \
    land_method_funs
from methods import apportion_sainte_lague
from division_rules import sainte_lague_gen
from running_stats import Running_stats, combine_stat
from util import disp
from result_tables import method_measure_table, measure_table, print_df
disp(width=60)
from time import sleep

def calc_share(votes):
    share = np.array([v[:,:-1]/np.sum(v,1)[:,None] for v in votes])
    return share

def randomize_votes(votes, partyvotes, cv, cvp, nsim):
    rng = np.random.default_rng()
    shape = 1/cv**2
    scale = 1/shape
    gv = []
    for i in range(len(votes)):
        size = (nsim,) + np.shape(votes[i])
        randvotes = rng.gamma(shape, scale, size=size)*votes[i]
        #randvotes = np.rint(randvotes).astype(int)
        gv.append(randvotes)
    shapep = 1/cvp**2
    scalep = 1/shape
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
                    options = ['mean', 'max', 'sum'])
    return running

def run_simulate(info, data, const_methods, land_methods, nsim):
    landseats = data["landseats"]
    partyvotes = data["partyvotes"]
    constvotes = data["constvotes"]
    const_meth = [cm for cm in const_method_dicts if cm['short'] in const_methods]
    land_meth = [lm for lm in land_method_dicts if lm['short'] in land_methods]
    (nland, nparty) = partyvotes.shape
    nparty -= 1
    nconst = [len(v) for v in constvotes]
    gv, gpv = randomize_votes(constvotes, partyvotes, cv, pcv, nsim)
    share = [calc_share(v) for v in gv]
    partyvote_share = calc_share(gpv)
    max_neg_margin = np.zeros(nland)
    neg_marg_freq = np.zeros(nland)
    min_seat_share = np.zeros(nland)
    parties = list(info["party"].values())
    #länder = list(info["land"].values())
    länder = list(land_abbrev.values())
    running = initialize_running(const_methods, land_methods, nland,nparty,parties,länder)
    for k in range(nsim):
        for const_method in const_methods:
            const_method_fun = const_method_funs[const_method]
            nat_vote_share = gpv[k].sum(axis=0)/gpv[k].sum()
            prop_party_seats = apportion_sainte_lague(nat_vote_share[:-1], 598)
            prop_party_seats = r_[prop_party_seats, 0]
            for land_method in land_methods:
                land_method_fun = land_method_funs[land_method]
                if land_method in {'party1st', 'land1st'}:
                    alloc = land_method_fun(gpv[k], prop_party_seats, landseats)
                else:
                    prior_alloc = np.zeros(gpv[k].shape, int)
                    party_seats, _ = land_method_fun (
                        gpv[k],
                        landseats,
                        prop_party_seats,
                        prior_alloc,
                        sainte_lague_gen)
                    alloc = np.array(party_seats)
                party_disparity = alloc.sum(axis=0) - prop_party_seats
                land_disparity = alloc.sum(axis=1) - landseats
                method = f"{const_method}-{land_method}"
                for l in range(nland):
                    voteshare = share[l][k]
                    selected = const_method_fun(voteshare, alloc[l, :])
                    I = range(nconst[l])
                    neg_margin = voteshare.max(axis=1) - voteshare[I, selected]
                    max_neg_margin[l] = neg_margin.max()
                    neg_marg_freq[l] = np.mean(neg_margin > 0)
                    min_seat_share[l] = min(voteshare[I, selected]).min()

                runmeth = running[method]
                runmeth['max_neg_margin'].update(max_neg_margin)
                runmeth['min_seat_share'].update(min_seat_share)
                runmeth['land_disparity'].update(land_disparity)
                runmeth['neg_marg_freq'].update(neg_marg_freq)
                runmeth['party_disparity'].update(party_disparity)
                if method == 'scand-votepct':
                    print('First running:', runmeth['scand-votepct']['party_disparity'])
        return running

def display_results(running):
    pass

def parallel_simulate(info, data, const_methods, land_methods, nsim, nproc):
    ntask = [nsim//nproc + (1 if i < nsim % nproc else 0) for i in range(nproc)]
    pool = Pool(nproc)
    stats = pool.map(run_simulate, [info]*nproc, [data]*nproc, [const_methods]*nproc,
                     [land_methods]*nproc, ntask)
    stat0 = stats.pop(0)
    for running in stats:
        combine_stat(stat0, running)
    return stat0

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
    if ncores == 1:
        running = run_simulate(info, data, const_methods, land_methods, nsim)
    else:
        running = parallel_simulate(info, data, const_methods, land_methods, nsim, ncores)
    mm_mean = method_measure_table(running, measure_formats, 'mean')
    mm_max = method_measure_table(running, measure_formats, 'max')
    method = 'land1st-votepct'
    lm = measure_table(running, measure_formats, 'votepct-party1st', 'land')
    pm = measure_table(running, measure_formats, 'votepct-land1st', 'party')
    for df in (mm_mean, mm_max, lm, pm):
        print_df(df, wrap_headers=True)
    pass
