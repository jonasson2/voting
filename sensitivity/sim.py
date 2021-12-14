#!/usr/bin/env python3
import sys
sys.path.append("../backend")
from multiprocessing import Pool
from noweb import load_votes, load_systems, single_election
from noweb import start_simulation, check_simulation, run_simulation, SIMULATIONS
from copy import deepcopy, copy
from datetime import datetime
import json
from util import disp, dispv
import numpy as np

n_proc         = 2
n_reps         = 1
n_gamma_sim    = n_proc*n_reps
n_unif_sim     = 100
inner_var_coef = 0.001

#vote_file = "aldarkosning.csv"
#vote_file = "2-by-2-example.csv"
#vote_file = "iceland-2021-first.csv"
#sys_file = "../data/tests/default-rule.json"
#sys_file = "~/hermir/2reglur.json"

vote_file = "21st-century-avg.csv"
sys_file = "10kerfi.json"

def read_data():
    votes = load_votes("../data/elections/" + vote_file)
    systems, sim_settings = load_systems(sys_file)
    return votes, systems, sim_settings

(votes, systems, sim_settings) = read_data()

def main():
    jsonfile, meanfile, stdfile, logfile = filenames()
    systemnames = [s["name"] for s in systems]
    with open(logfile,'w'):
        pass
    A = []
    S = []
    nsys = len(systems)
    pars = ((idx, logfile) for idx in range(n_proc))
    p = Pool(n_proc)
    results = p.starmap(simulate, pars)
    
    for result in results:
        A.extend([r for r in result[0]])
        S.extend([r for r in result[1]])
        
    metadata = {
        "n_gamma_sim":     n_gamma_sim,
        "n_unif_sim":      n_unif_sim,
        "system_file":     sys_file,
        "vote_file":       vote_file,
        "system_names":    systemnames,
        "outer_settings":  sim_gamma_settings(),
        "inner_settings":  sim_unif_settings(),
    }
    with open(jsonfile, 'w', encoding='utf-8') as fd:
        json.dump(metadata, fd, ensure_ascii=False, indent=2)
    writecsv(meanfile, A)
    writecsv(stdfile, S)    

def filenames():
    from pathlib import Path
    if len(sys.argv) > 1:
        filestem = sys.argv[1]
    else:
        date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
        filestem=f"simresults-{date}"
    filestem = "results/" + filestem    
    jsonfile = filestem + ".json"
    meanfile = filestem + ".m.csv"
    stdfile = filestem + ".s.csv"
    logfile = filestem + ".log"
    return jsonfile, meanfile, stdfile, logfile

def read_data():
    # Read votes table and electoral systems to simulate
    votes = load_votes("../data/elections/" + vote_file)
    systems, sim_settings = load_systems(sys_file)
    # results = single_election(votes, systems)
    # disp("votes", votes)
    # disp("systems", systems) (is included in results)
    # disp("results", results)
    return votes, systems, sim_settings

def simulate_votes(votes, systems, sim_settings):
    # Run one step of simulation and return the simulated votes
    settings = copy(sim_settings)
    assert settings["simulation_count"] == 1
    results = run_simulation(votes, systems, settings)
    return results["vote_data"][0]["sim_votes"]["avg"]

def matrix2votes(A):
    # Remove total columns and round votes to integers
    B = [[round(x) for x in a[:-1]] for a in A[:-1]]
    return B

def get_sim_settings(sim_settings, gen_method, *, dist_param=None, nsim=None):
    # Return version of sim_settings with specified changes
    # e.g. get_sim_settings(sim_settings, nsim=300)
    settings = deepcopy(sim_settings)
    settings["gen_method"] = gen_method
    if dist_param != None: settings["distribution_parameter"] = dist_param
    if nsim       != None: settings["simulation_count"] = nsim
    return settings

def sim_gamma_settings():
    return get_sim_settings(sim_settings, "gamma", dist_param=0.25, nsim=1)

def sim_unif_settings():
    return get_sim_settings(sim_settings, "uniform", dist_param=inner_var_coef,
                            nsim = n_unif_sim)

def colmean(A):
    # Return column means of "non-numpy" Matrix
    m = len(A)
    n = len(A[0])
    avg = [0.0]*n
    for i in range(n):
        avg[i] = sum([a[i] for a in A])/m
    return avg

def writecsv(file,L):
    import csv
    with open(file, "w") as f:
        writer = csv.writer(f)
        writer.writerows(L)

def simulate(idx, logfile):
    import socket
    host = socket.gethostname()
    print(idx,logfile)
    sim_votes = deepcopy(votes)
    nsys = len(systems)
    avg = []
    std = []
    for idx_gamma in range(n_reps):
        if idx==0:
            with open(logfile, 'a') as logf:
                for f in [sys.stdout, logf]:
                    print(f"Host {host}, rep {idx_gamma+1} out of {n_reps}", file=f)
        matrix = simulate_votes(votes, systems, sim_gamma_settings())
        sim_votes["votes"] = matrix2votes(matrix)
        res = run_simulation(sim_votes, systems, sim_unif_settings(),
                             sensitivity = True)
        dev_ref_avg = [res["data"][i]["measures"]["dev_ref"]["avg"]
                       for i in range(nsys)]
        dev_ref_std = [res["data"][i]["measures"]["dev_ref"]["std"]
                       for i in range(nsys)]
        avg.append(dev_ref_avg)
        std.append(dev_ref_std)
    return avg,std

if __name__ == "__main__":
    main()
