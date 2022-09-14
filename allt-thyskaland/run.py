#!/usr/bin/env python3
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
from dictionaries import land_methods, const_methods, short_land_methods, \
    short_const_methods, party_measures, land_measures, short_party_measures, \
    short_land_measures, measures, land_abbrev, measure_formats
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
            for measure in short_party_measures:
                running[method][measure] = Running_stats (
                    shape = nparty + 1,
                    names = parties,
                    options = ['mean', 'max', 'min', 'sum'])
            for measure in short_land_measures:
                running[method][measure] = Running_stats(
                    shape = nland,
                    names = länder,
                    options = ['mean', 'max', 'sum'])
    return running

def run_simulate(info, data, methods, nsim):
    landseats = data["landseats"]
    partyvotes = data["partyvotes"]
    constvotes = data["constvotes"]
    const_meth = [cm for cm in const_methods if cm['short'] in methods['cm']]
    land_meth = [lm for lm in land_methods if lm['short'] in methods['lm']]
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
    running = initialize_running(short_const_methods, short_land_methods, nland, nparty,
                                 parties, länder)
    for k in range(nsim):
        print('k=', k)
        for cm in const_meth:
            const_method = cm['fun']
            nat_vote_share = gpv[k].sum(axis=0)/gpv[k].sum()
            prop_party_seats = apportion_sainte_lague(nat_vote_share[:-1], 598)
            prop_party_seats = r_[prop_party_seats, 0]
            for lm in land_meth:
                land_method = lm['fun']
                if lm['short'] in {'party1st', 'land1st'}:
                    alloc = land_method(gpv[k], prop_party_seats, landseats)
                else:
                    prior_alloc = np.zeros(gpv[k].shape, int)
                    party_seats, _ = land_method(gpv[k],
                                                 landseats,
                                                 prop_party_seats,
                                                 prior_alloc,
                                                 sainte_lague_gen)
                    alloc = np.array(party_seats)
                party_disparity = alloc.sum(axis=0) - prop_party_seats
                land_disparity = alloc.sum(axis=1) - landseats
                method = f"{cm['short']}-{lm['short']}"
                for l in range(nland):
                    voteshare = share[l][k]
                    selected = const_method(voteshare, alloc[l, :])
                    I = range(nconst[l])
                    neg_margin = voteshare.max(axis=1) - voteshare[I, selected]
                    max_neg_margin[l] = neg_margin.max()
                    neg_marg_freq[l] = np.mean(neg_margin > 0)
                    min_seat_share[l] = min(voteshare[I, selected]).min()

                for measure in land_measures + party_measures:
                    runnmeth = running[method]
                    runnmeth['max_neg_margin'].update(max_neg_margin)
                    runnmeth['min_seat_share'].update(min_seat_share)
                    runnmeth['land_disparity'].update(land_disparity)
                    runnmeth['neg_marg_freq'].update(neg_marg_freq)
                    runnmeth['party_disparity'].update(party_disparity)
    return running

def display_results(running):
    pass

def parallel_simulate(info, data, methods, nsim, nproc):
    ntask = [nsim//nproc + (1 if i < nsim % nproc else 0) for i in range(nproc)]
    pool = Pool(nproc)
    stats = pool.map(run_simulate, [info]*nproc, [data]*nproc, [methods]*nproc, ntask)
    stat0 = stats.pop(0)
    for running in stats:
        combine_stat(stat0, running)
    return stat0

if __name__ == "__main__":

    # NÁ Í SKIPANALÍNUVIÐFÖNG
    pm_list = '/'.join(short_land_methods) + '/all'
    cm_list = '/'.join(short_const_methods) + '/all'
    args = [
       ['nsim', int, 'total number of simulations', 5],
       ['-ncores', int, 'number of cores', 8],
       ['-erstmethod', str, f'method for constituency votes [{cm_list} or all]', 'all'],
       ['-zweitmethod', str, f'method for party votes [{pm_list} or all]', 'all'],
       ['-cv', float, 'variation coefficient for constituency vote generation',  0.3],
       ['-pcv', float, 'variation coefficient for party vote generation', 0.1]]
    desc = "Simulate for the whole of Germany"
    (nsim, ncores, erst, zweit, cv, pcv) = get_arguments(args=args, description=desc)
    methods = {}
    methods["cm"] = short_const_methods if erst == 'all' else erst.split(',')
    methods["lm"] = short_land_methods if zweit == 'all' else zweit.split(',')

    info, data = readkerg()

    # RUN THE SIMULATION
    if ncores == 1:
        running = run_simulate(info, data, methods, nsim)
    else:
        running = parallel_simulate(info, data, methods, nsim, ncores)
    mm_mean = method_measure_table(running, measure_formats, 'mean')
    mm_max = method_measure_table(running, measure_formats, 'max')
    method = 'land1st-votepct'
    lm = measure_table(running, measure_formats, 'votepct-party1st', 'party')
    pm = measure_table(running, measure_formats, 'votepct-land1st', 'land')
    for df in (mm_mean, mm_max, lm, pm):
        print_df(df, wrap_headers=True)
    pass
