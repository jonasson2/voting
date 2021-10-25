from noweb import load_votes, load_systems, single_election
from noweb import start_simulation, check_simulation, SIMULATIONS
from time import sleep
from math import sqrt
from copy import deepcopy

import json

def disp(title, value, depth=99):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(compact=False, width=80, depth=depth).pprint
    print("\n" + title.upper() + ":")
    pp(value)

def read_data():
    # votes = load_votes("iceland-2021-first.csv", preset=True)
    sys1, sim_settings = load_systems("lögin.json")
    #vote_file = "../data/elections/aldarkosning.csv"
    sys_file = "11kerfi.json"
    vote_file = "../data/elections/2-by-2-example.csv"
    #sys_file = "../data/tests/default-rule.json"
    votes = load_votes(vote_file)
    systems, _ = load_systems(sys_file)
    results = single_election(votes, systems)
    # disp("votes", votes)
    # disp("systems", systems) (is included in results)
    return votes, sys1, systems, sim_settings

def simulate_votes(votes, systems, sim_settings):
    sid = start_simulation(votes, systems, sim_settings)
    status,results = check_simulation(sid, False)
    while not status["done"]:
        print("X",end="")
        sleep(0.001)
        status, results = check_simulation(sid, False)
    return results["vote_data"]["sim_votes"]["avg"]

def simulate(votes, systems, sim_settings):
    print("simulate")
    sid = start_simulation(votes, systems, sim_settings)
    status,_ = check_simulation(sid, False)
    i = 0;
    while not status["done"]:
        sleep(0.1)
        status, results = check_simulation(sid, False)
    return results

def matrix2votes(A):
    B = [[round(x) for x in a[:-1]] for a in A[:-1]]
    return B

def get_sim_settings(sim_settings, gen_method, dist_param, nsim):
    settings = deepcopy(sim_settings)
    settings["gen_method"] = gen_method
    settings["distribution_parameter"] = dist_param
    settings["simulation_count"] = nsim
    return settings

n = 100

(votes, sys1, systems, sim_settings) = read_data()
sim_beta_settings = get_sim_settings(sim_settings, "beta", 0.25, 100)
sim_unif_settings = get_sim_settings(sim_settings, "uniform", 0.01/sqrt(3), n)

sim_votes = deepcopy(votes)

for idx_total in range(1):
    for idx_beta in range(1):
        matrix = simulate_votes(votes, sys1, sim_beta_settings)
        disp("matrix", matrix)
        disp("sim_votes", sim_votes)
        #sim_votes["votes"] = matrix2votes(matrix)
        disp("sim_votes", sim_votes)
        #results = simulate(sim_votes, systems, sim_unif_settings);
#disp('results[vote_data]', results["vote_data"], depth=6)

#disp("votes", votes)
#disp("sim_votes", sim_votes)
# n = len(systems)
# disp("results", results, depth=4)
# disp("dev_ref", results["measures"]["dev_ref"])
# dr = [results["data"][i]["measures"] for i in range(n)]
# disp("dr", dr)
#disp("tot_dev_ref", results["totals_deviation_measures"])

#disp("sim_votes", sim_votes)
#disp("data", results["data"], depth=2)
#disp("vote_data", results["vote_data"]["sim_votes"]["avg"], depth=3)
