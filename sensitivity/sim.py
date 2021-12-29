#!/usr/bin/env python3
import sys, math, random
sys.path.append("../backend")
import multiprocessing as mp
from multiprocessing import Pool
from noweb import load_votes, load_systems, single_election
from noweb import start_simulation, check_simulation, run_simulation, SIMULATIONS
from histogram import combine_counts
from copy import deepcopy, copy
from datetime import datetime
import json
from util import disp, dispv
import numpy as np

#vote_file = "aldarkosning.csv"
#vote_file = "2-by-2-example.csv"
vote_file = "iceland-2021-first.csv"
#sys_file = "../data/tests/default-rule.json"
#sys_file = "~/hermir/2reglur.json"

#vote_file = "21st-century-avg.csv"
sys_file = "10kerfi.json"

def get_arguments():
    from argparse import ArgumentParser
    p = ArgumentParser(description = "Simulate sensitivity of elections")
    args = [
        ['n_reps',   10,   int,   'total number of simulations'],
        ['n_cores',  1,    int,   'number of cores'],
        ['-sens_cv', 0.01, float, 'coefficient of variation for shake'],
        ['-cv',      0.25, float, 'variation coefficient for vote generation'],
        ['-folder',  '',   str,   'default is the fractional part of sens_cv']]
    for (name, default, type, help) in args:
        p.add_argument(name, default=default, type=type, help=help)
    n = p.parse_intermixed_args()
    if not n.folder:
        n.folder = f'{n.sens_cv}'[2:]
    return (n.n_reps, n.n_cores, n.sens_cv, n.cv, n.folder)

def read_data():
    votes = load_votes("../data/elections/" + vote_file)
    systems, sim_settings = load_systems(sys_file)
    return votes, systems, sim_settings

def set_sim_settings(sim_settings, n_sim, sens_cv, cv):
    settings = deepcopy(sim_settings)
    settings["simulation_count"] = n_sim
    settings["distribution_parameter"] = cv
    settings["sens_cv"] = sens_cv
    settings["sensitivity"] = True
    return settings

def filenames(folder, n_cores, n_sim):
    from pathlib import Path
    import socket, time
    host = socket.gethostname()
    # now = datetime.now().strftime('%Y.%m.%dT%H.%M')
    result_folder = Path.home() / 'runpar' / host / folder
    result_folder.mkdir(parents=True, exist_ok=True)
    jsonfile = result_folder / "meta.json"
    histfile = result_folder / "h.csv"
    logfile = result_folder / "sim.log"
    with open(logfile, 'w') as logf:
        def log(s): print(s, file=logf)
        log(f'Host: {host}')
        log(f'Time: {time.time}')
        log(f'n_cores: {n_cores}')
        log(f'reps/core: {n_sim}')
    return jsonfile, histfile, logfile

(votes, systems, sim_settings) = read_data()
(n_reps, n_cores, sens_cv, cv, folder) = get_arguments()
n_sim = math.ceil(n_reps/n_cores)
sim_settings = set_sim_settings(sim_settings, n_sim, sens_cv, cv)
(jsonfile, histfile, logfile) = filenames(folder, n_cores, n_sim)

def histograms2array(hist_list):
    # Creates a list of count lists from a list of histogram dictionaries. All the count
    # lists have the same length, filling with zeros where needed.
    histarray = []
    if not hist_list:
        keymax = 0
    else:
        keymax = max(max(h.keys()) for h in hist_list) + 1
    for hist in hist_list:
        L = [0]*keymax
        for (k,v) in hist.items():
            L[k] = v
        histarray.append(L)
    return histarray

def combine_histogram_lists(hist_list):
    # Combine list of histogram lists [L0,L1...] into a list of histograms, [H0,H1...]:
    # H0 is the combined histogram for L0[0], L1[0]..., H1 combines L0[1], L1[1], etc.
    # There is one L-list for each core and one H-histogram for each system.
    nsys = len(systems)
    combined_list = []
    for i in range(nsys):
        h = combine_counts(h[i] for h in hist_list)
        combined_list.append(h)
    return combined_list

def main():
    #random.seed(11)
    sim_settings["sensitivity"] = True
    systemnames = [s["name"] for s in systems]
    pars = range(n_cores)
    if n_cores > 1:
        p = Pool(n_cores)
        results = p.map(simulate, pars)
    else:
        results = [simulate(0)]
    hist = combine_histogram_lists(results)
    hist_array = histograms2array(hist)

    metadata = {
        "n_reps":        n_reps,
        "system_file":   sys_file,
        "vote_file":     vote_file,
        "system_names":  systemnames,
        "sim_settings":  sim_settings,
    }
    with open(jsonfile, 'w', encoding='utf-8') as fd:
        json.dump(metadata, fd, ensure_ascii=False, indent=2)
    print(histfile)
    writecsv(histfile, hist_array)

def writecsv(file,L):
    import csv
    with open(file, "w") as f:
        writer = csv.writer(f)
        writer.writerows(L)
        
def simulate(idx):
    logfile0 = logfile if idx == 0 else None
    list_sens,_ = run_simulation(votes, systems, sim_settings, logfile=logfile0)
    #party_sens = np.array(ps)
    return list_sens

if __name__ == "__main__":
    main()
