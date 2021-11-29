import sys
sys.path.append("..")
from noweb import load_votes, load_systems, single_election
from noweb import start_simulation, check_simulation, SIMULATIONS
from noweb import simulation_to_excel, run_simulation
from electionHandler import update_constituencies
from time import sleep
import json

def disp(title, value, depth=99):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(compact=False, width=100, depth=depth).pprint
    print("\n" + title.upper() + ":")
    pp(value)

# vote_table = load_votes("iceland-2021-first.csv", preset=True)
# vote_table = load_votes("../data/elections/aldarkosning.csv")
# vote_table = load_votes("../data/elections/2-by-2-example.csv")
vote_table = load_votes("3-by-2-example.csv")
# vote_table["votes"][0][0] = 0

# systemfile = "1regla.json"
# systemfile = "11reglur.json"
# systemfile = "2reglur.json"
systemfile = "5sys-for-testing.json"

systems, sim_settings = load_systems(systemfile)
constituencies = update_constituencies(vote_table, systems)
disp("constituencies", constituencies)

single_results = single_election(vote_table, systems)
disp("single_results", single_results)
# results = single_election(vote_table, systems)
# disp("votes", vote_table)
# disp("systems", systems) (is included in results)
# sim_settings["simulation_count"] = 10
# results = run_simulation(vote_table, systems, sim_settings, "a.xlsx")
# results = run_simulation(vote_table, systems, sim_settings)
# disp("sim_results", results["vuedata"])
