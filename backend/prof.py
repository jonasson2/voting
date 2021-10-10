from web import *
from time import sleep
import json

def disp(title, value):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(compact=False, width=80).pprint
    print("\n" + title.upper() + ":")
    pp(value)

if __name__ == "__main__":
    votes = load_preset_votes("2-by-2-example.csv")
    file = "~/Downloads/1regla.json"    
    rules, sim_settings = load_settings(file)
    results = single_election(votes, rules)
    #disp("votes", votes)
    #disp("rules", rules) (is included in results)
    disp("sim_settings", sim_settings)
    disp("results", results)
    sid = set_up_simulation(votes, rules, sim_settings)
    while True:
        sleep(0.2)
        status, results = monitor_simulation(sid, False)
        disp("status", status)
        if status["done"]: break
