from web import *
import json

def disp(s):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(compact=False, width=80).pprint
    print("\n" + s.upper() + ":")
    pp(eval(s))

if __name__ == "__main__":
    votes = load_preset_votes("iceland-2021.csv")
    file = "~/Downloads/2reglur.json"    
    rules, sim_settings = load_settings(file)
    results = single_election(votes, rules)
    #disp("votes")
    #disp("rules") (is included in results)
    disp("sim_settings")
    #disp("results")
    start_simulation()
