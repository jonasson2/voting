from noweb import load_votes, load_systems, single_election
from noweb import start_simulation, check_simulation, SIMULATIONS
from time import sleep
import json

def disp(title, value, depth=99):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(compact=False, width=80, depth=depth).pprint
    print("\n" + title.upper() + ":")
    pp(value)

if __name__ == "__main__":
    votes = load_votes("iceland-2021-first.csv", preset=True)
    # votes = load_votes("~/voting/data/tests/Aldarkosning.xlsx")
    systemfile = "rule.json"    
    systems, sim_settings = load_systems(systemfile)
    results = single_election(votes, systems)
    # disp("votes", votes)
    # disp("systems", systems) (is included in results)
    sim_settings["simulation_count"] = 100
    disp("sim_settings", sim_settings)
    #disp("results", results)
    sid = start_simulation(votes, systems, sim_settings)
    status,_ = check_simulation(sid, False)
    totiter = sim_settings["simulation_count"]
    while not status["done"]:
        sleep(1)
        status, results = check_simulation(sid, False)
        iter = status["iteration"]
        #disp("status", status)
        print(f"Iterations: {iter} of {totiter}")
    disp("results", results["data"][0]["measures"]["dev_ref"], depth=6)
