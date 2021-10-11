import threading
import random
import os
from datetime import datetime, timedelta
import json
from hashlib import sha256
from electionRules import ElectionRules
from electionHandler import ElectionHandler
import util
from input_util import check_input, check_rules, check_simulation_rules
import simulate

def load_votes(file, preset=True):
    if preset: file = "../data/elections/" + file
    res = util.load_votes_from_stream(open(file, "r"), file)
    return res

def load_settings(f):
    if isinstance(f,str):
        f = os.path.expanduser(f)
        with open(f) as file: file_content = json.load(file)
    else:
        file_content = json.load(f.stream)
    if type(file_content) == dict and "e_settings" in file_content:
        electoral_system_list = file_content["e_settings"]
        assert "sim_settings" in file_content
        sim_settings = check_simulation_rules(file_content["sim_settings"])
    else:
        electoral_system_list = file_content
        sim_settings = None
    assert type(electoral_system_list) == list

    keys = ["name", "seat_spec_option", "constituencies",
            "constituency_threshold", "constituency_allocation_rule",
            "adjustment_threshold", "adjustment_division_rule",
            "adjustment_method", "adjustment_allocation_rule"]
    settings = []
    for item in electoral_system_list:
        for info in keys:
            if info not in item:
                raise KeyError(f"{info} is missing from a setting in file.")
        if item["seat_spec_option"] == "defer":
            item["seat_spec_option"] = "refer"
        setting = ElectionRules()
        setting.update(item)
        setting["primary_divider"] = item["constituency_allocation_rule"]
        setting["adj_determine_divider"] = item["adjustment_division_rule"]
        setting["adj_alloc_divider"] = item["adjustment_allocation_rule"]
        settings.append(setting)

    settings = check_rules(settings)
    return settings, sim_settings
    
def single_election(votes, rules):
    result = ElectionHandler(votes, rules).elections
    results = [election.get_results_dict() for election in result]
    return results

def run_simulation(sid):
    global SIMULATIONS
    (sim, thread, _) = SIMULATIONS[sid]
    thread.done=False
    #print("Starting thread %s" % sid)
    sim.simulate()
    #print("Ending thread %s" % sid)
    thread.done = True

def start_simulation(votes, rules, sim_settings):
    global SIMULATIONS
    global SIMULATION_IDX
    SIMULATION_IDX += 1
    h = sha256()
    sidbytes = (str(SIMULATION_IDX) + ":" + str(random.randint(1, 100000000))).encode('utf-8')
    h.update(sidbytes)
    sid = h.hexdigest()
    rulesets = []
    for rs in rules:
        election_rules = ElectionRules()
        election_rules.update(rs)
        rulesets.append(election_rules)
    simulation_rules = simulate.SimulationRules()
    simulation_rules.update(check_simulation_rules(sim_settings))
    simulation = simulate.Simulation(simulation_rules, rulesets, votes)
    cleanup_expired_simulations()
    expires = datetime.now() + timedelta(seconds=24*3600) # 24 hrs
    # Allt þetta "expiry" þarf eitthvað að skoða og hugsa
    thread = threading.Thread(target=run_simulation, args=(sid,))
    SIMULATIONS[sid] = [simulation, thread, expires]
    thread.start()
    return sid

def check_simulation(sid, stop):
    (sim, thread, _) = SIMULATIONS[sid]
    sim.iteration -= sim.iterations_with_no_solution
    sim_status = {
        "done": thread.done,
        "iteration": sim.iteration,
        "time_left": sim.time_left,
        "total_time": sim.total_time,
        "target": sim.sim_rules["simulation_count"],
    }
    sim_results = sim.get_results()
    if stop:
        sim.terminate = True
        # thread.join() finishes the thread and sets thread.done to True
        thread.join()
    return sim_status, sim_results

def cleanup_expired_simulations():
    global SIMULATIONS
    try:
        for sid in SIMULATIONS:
            expires = SIMULATIONS[sid][2]
            if expires < datetime.now():
                del(SIMULATIONS[sid])
    except RuntimeError:
        pass

def get_new_download_id():
    global DOWNLOADS_IDX
    did = DOWNLOADS_IDX = DOWNLOADS_IDX + 1
    h = sha256()
    didbytes = (str(did) + ":" + str(random.randint(1, 100000000))).encode('utf-8')
    h.update(didbytes)
    return h.hexdigest()

SIMULATIONS = {}
SIMULATION_IDX = 0

