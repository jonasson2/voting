import sys
sys.path.append("..")
from noweb import load_votes, load_systems, single_election
from noweb import start_simulation, check_simulation, SIMULATIONS
from noweb import simulation_to_excel, run_simulation
from time import sleep
DATA = "../../data/"
ELEC = DATA + "elections/"

import json

def disp(title, value, depth=99):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(compact=False, width=100, depth=depth).pprint
    print("\n" + title.upper() + ":")
    pp(value)

vote_table = load_votes("iceland-2021-first.csv", preset=True)
# vote_table = load_votes(ELEC + "aldarkosning.csv")
# vote_table = load_votes(ELEC + "2-by-2-example.csv")
# systemfile = "1regla.json"
# vote_table["votes"][0][0] = 0
systemfile = "newtest/2reglur.json"
systems, sim_settings = load_systems(systemfile)

#single_results,const = single_election(vote_table, systems)
# results = single_election(vote_table, systems)
# disp("vote_table", vote_table)
# disp("systems", systems) (is included in results)
sim_settings["simulation_count"] = 100
# results = run_simulation(vote_table, systems, sim_settings, "a.xlsx")
results = run_simulation(vote_table, systems, sim_settings)
disp("results", results["vuedata"])
