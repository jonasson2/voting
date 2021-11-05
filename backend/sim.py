from multiprocessing import Pool
from noweb import load_votes, load_systems, single_election
from noweb import start_simulation, check_simulation, run_simulation, SIMULATIONS
from time import sleep
from math import sqrt
from copy import deepcopy, copy
import json
n_reps = 1
n_betasim = 1
n_unifsim = 1

def disp(title, value, depth=99):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(compact=False, width=120, depth=depth).pprint
    print("\n" + title.upper() + ":")
    pp(value)

def read_data():
    # Read votes table and electoral systems to simulate
    #vote_file = "aldarkosning.csv"
    vote_file = "2-by-2-example.csv"
    #vote_file = "aldarkosning.csv"
    #sys_file = "11kerfi.json"
    #sys_file = "../data/tests/default-rule.json"
    sys_file = "2reglur.json"
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
    settings["simulation_count"] = 1
    print("In simulate_votes")
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

(votes, systems, sim_settings) = read_data()
# disp("systems", systems)
sim_beta_settings = get_sim_settings(sim_settings, "beta",    dist_param=0.25)
sim_unif_settings = get_sim_settings(sim_settings, "uniform", dist_param=0.01, nsim=n_unifsim)

def colmean(A):
    # Return column means of "non-numpy" Matrix
    m = len(A)
    n = len(A[0])
    avg = [0.0]*n
    for i in range(n):
        avg[i] = sum([a[i] for a in A])/m
    return avg

def printcsv(file,L):
    import csv
    with open(file, "w") as f:
        writer = csv.writer(f)
        writer.writerows(L)

def simulate(idx):
    sim_votes = deepcopy(votes)
    nsys = len(systems)
    avg = []
    std = []
    for idx_beta in range(n_betasim):
        #disp("votes", votes)
        matrix = simulate_votes(votes, systems, sim_beta_settings)
        #disp("matrix", matrix)
        sim_votes["votes"] = matrix2votes(matrix)
        #disp("sim_votes", sim_votes)
        #disp("systems", systems)
        #disp("sim_unif_settings", sim_unif_settings)
        res = run_simulation(sim_votes, systems, sim_unif_settings)
        dev_ref_avg = [res["data"][i]["measures"]["dev_ref"]["avg"]
                       for i in range(nsys)]
        dev_ref_std = [res["data"][i]["measures"]["dev_ref"]["std"]
                       for i in range(nsys)]
        disp("dev_ref_avg", dev_ref_avg)
        avg.append(dev_ref_avg)
        std.append(dev_ref_std)
    disp("res", res)
    A = colmean(avg)
    S = colmean(std)
    return A,S

systemnames = [s["name"] for s in systems]

#sim_beta_settings["simulate"] = True
disp("sim_beta_settings", sim_beta_settings)
matrix = simulate_votes(votes, systems, sim_beta_settings)
result = simulate(1)
if False: #__name__ == "__main__":
    nsys = len(systems)
    p = Pool(n_reps)
    #result = p.map(simulate, list(range(n_reps)))
    result = [simulate(1)]
    means = [r[0] for r in result]
    sdevs = [r[1] for r in result]
    printcsv("means.dat", means)
    printcsv("sdevs.dat", sdevs)
    #disp("means", means)
    #plot(means, systemnames)
