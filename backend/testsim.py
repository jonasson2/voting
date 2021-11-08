from noweb import load_votes, load_systems, single_election
from noweb import start_simulation, check_simulation, SIMULATIONS
from noweb import simulation_to_excel, run_simulation
from time import sleep
import json

def disp(title, value, depth=99):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(compact=False, width=200, depth=depth).pprint
    print("\n" + title.upper() + ":")
    pp(value)

# votes = load_votes("iceland-2021-first.csv", preset=True)
votes = load_votes("../data/elections/aldarkosning.csv")
systemfile = "2reglur.json"
systems, sim_settings = load_systems(systemfile)
# results = single_election(votes, systems)
# disp("votes", votes)
# disp("systems", systems) (is included in results)
sim_settings["simulation_count"] = 10
# disp("sim_settings", sim_settings)
results = run_simulation(votes, systems, sim_settings, "a.xlsx")
#disp("results", results)
