from multiprocessing import Pool
from noweb import load_votes, load_systems, single_election
from noweb import start_simulation, check_simulation, run_simulation, SIMULATIONS
from time import sleep
from math import sqrt
from copy import deepcopy, copy
import numpy as np
import numpy.random as npr

n_reps = 4
n_betasim = 1
n_unifsim = 2

np.set_printoptions(precision=3, floatmode = 'fixed', suppress=True)

import json

def disp(title, value, depth=99):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(compact=False, width=120, depth=depth).pprint
    print("\n" + title.upper() + ":")
    pp(value)

def read_data():
    # Read votes table and electoral systems to simulate
    #vote_file = "aldarkosning.csv"
    #vote_file = "../data/elections/2-by-2-example.csv"
    vote_file = "iceland-2021-first.csv"
    sys_file = "11kerfi.json"
    #sys_file = "../data/tests/default-rule.json"
    #sys_file = "1regla.json"
    votes = load_votes("../data/elections/" + vote_file)
    systems, sim_settings = load_systems(sys_file)
    results = single_election(votes, systems)
    # disp("votes", votes)
    # disp("systems", systems) (is included in results)
    return votes, systems, sim_settings

def simulate_votes(votes, systems, sim_settings):
    # Run one step of simulation and return the simulated votes
    settings = copy(sim_settings)
    settings["simulation_count"] = 1
    results = run_simulation(votes, systems, settings)
    return results["vote_data"]["sim_votes"]["avg"]

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

def plot(results, names):
    # Plot an arrray of histograms of results, one for each electoral system.
    # Each histogram describes the distribution of the n_reps dev_ref average
    # values and each such value is the average over the n_betasim*n_unifsim
    # simulated election results. Can also histogram standard deviations,
    # and then each value is the average of n_betasim standard deviations.
    import matplotlib.pyplot as plt
    import math
    results = np.array(results)
    plt.rc('savefig',bbox='tight')
    (nreps, nsys) = np.shape(results)
    sr = round(np.sqrt(nsys))
    sc = math.ceil(nsys/sr)
    plt.figure(figsize=(10,8))
    xmax = math.ceil(results.max())
    ylims = np.zeros(nsys)
    ax = []
    for j in range(nsys):
        rj = results[:,j]        
        axj = plt.subplot(sr, sc, j+1)
        ax.append(axj)
        plt.hist(rj, bins=xmax, range = (0,xmax), rwidth=0.8)
        plt.xlabel(names[j])
        ylims[j] = plt.gca().get_ylim()[1]
    ylim = max(ylims)
    for j in range(nsys): # Let all plots have same ylim:
        plt.sca(ax[j])
        plt.ylim(0, ylim)
    plt.tight_layout()
    plt.savefig('plot.png')

(votes, systems, sim_settings) = read_data()
# disp("systems", systems)
sim_beta_settings = get_sim_settings(sim_settings, "beta",    dist_param=0.0000001)
sim_unif_settings = get_sim_settings(sim_settings, "uniform", dist_param=0.002, nsim=n_unifsim)

def simulate(idx):
    sim_votes = deepcopy(votes)
    nsys = len(systems)
    avg = []
    std = []
    for idx_beta in range(n_betasim):
        #disp("votes", votes)
        matrix = simulate_votes(votes, systems[:1], sim_beta_settings)
        #disp("matrix", matrix)
        sim_votes["votes"] = matrix2votes(matrix)
        #disp("sim_votes", sim_votes)
        #disp("systems", systems)
        #disp("sim_unif_settings", sim_unif_settings)
        res = run_simulation(sim_votes, systems, sim_unif_settings)      
        dev_ref_avg = [res["data"][i]["measures"]["dev_ref"]["avg"] for i in range(nsys)]
        dev_ref_std = [res["data"][i]["measures"]["dev_ref"]["std"] for i in range(nsys)]
        avg.append(dev_ref_avg)
        std.append(dev_ref_std)
    A = np.array(avg).mean(axis=0)
    S = np.array(std).mean(axis=0)
    return A,S

systemnames = [s["name"] for s in systems]

if __name__ == "__main__":
    nsys = len(systems)
    p = Pool(n_reps)
    result = p.map(simulate, list(range(n_reps)))
    #disp("result", result)    
    means = [r[0] for r in result]
    sdevs = [r[1] for r in result]
    assert(np.array_equal(np.shape(means), (n_reps, nsys)))
    plot(means, systemnames)
