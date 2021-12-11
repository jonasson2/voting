import threading
import random
import os
from datetime import datetime, timedelta
import json
from hashlib import sha256
from electionSystem import ElectionSystem
from electionHandler import ElectionHandler, update_constituencies
import util
from util import disp
from input_util import check_input, check_systems, check_simul_settings
import simulate

from sim_measures import add_vuedata

def load_votes(f, preset=False):
    import os
    if preset: f = "../data/elections/" + f
    res = util.load_votes_from_stream(open(f, "r"), f)
    return res

def load_all(f):
    if isinstance(f,str):
        f = os.path.expanduser(f)
        with open(f) as file: file_content = json.load(file)
    else:
        file_content = json.load(f.stream)
    return file_content

def load_systems(f):
    '''returns systems, sim_settings from file json-file f'''
    if isinstance(f,str):
        f = os.path.expanduser(f)
        with open(f) as file: file_content = json.load(file)
    else:
        file_content = json.load(f.stream)
    if type(file_content) == dict and "e_settings" in file_content:
        electoral_system_list = file_content["e_settings"]
        assert "sim_settings" in file_content
        sim_settings = check_simul_settings(file_content["sim_settings"])
    else:
        electoral_system_list = file_content
        sim_settings = None
    assert type(electoral_system_list) == list
    #disp("esl", electoral_system_list)

    keys = ["name", "seat_spec_option", "constituencies",
            "constituency_threshold", "constituency_allocation_rule",
            "adjustment_threshold", "adjustment_division_rule",
            "adjustment_method", "adjustment_allocation_rule"]
    systems = []
    for item in electoral_system_list:
        for info in keys:
            if info not in item:
                raise KeyError(f"{info} is missing from a system in file.")
        if item["seat_spec_option"] == "refer":
            item["seat_spec_option"] = "refer"
        system = ElectionSystem()
        system.update(item)
        system["primary_divider"] = item["constituency_allocation_rule"]
        system["adj_determine_divider"] = item["adjustment_division_rule"]
        system["adj_alloc_divider"] = item["adjustment_allocation_rule"]
        systems.append(system)

    systems = check_systems(systems)
    return systems, sim_settings

def single_election(votes, systems):
    '''obtain results from single election for specific votes and a
    list of electoral systems'''
    elections = ElectionHandler(votes, systems, min_votes=0.5).elections
    results = [election.get_results_dict() for election in elections]
    return results

def run_thread_simulation(sid):
    global SIMULATIONS
    (sim, thread, _) = SIMULATIONS[sid]
    thread.done=False
    sim.simulate()
    thread.done = True

def run_simulation(votes, systems, sim_settings, excelfile = None):
    # not threaded
    # sim_settings = simulate.SimulationSettings()
    sim_settings.update(check_simul_settings(sim_settings))
    sim = simulate.Simulation(sim_settings, systems, votes)
    sim.simulate()
    if excelfile != None:
        sim.to_xlsx(excelfile)
    results = sim.get_results_dict()
    add_vuedata(results)
    return results

def start_simulation(votes, systems, sim_settings):
    global SIMULATIONS
    global SIMULATION_IDX
    SIMULATION_IDX += 1
    h = sha256()
    sidbytes = (str(SIMULATION_IDX) + ":"
                + str(random.randint(1, 100000000))).encode('utf-8')
    h.update(sidbytes)
    sid = h.hexdigest()
    simulation = simulate.Simulation(sim_settings, systems, votes)
    cleanup_expired_simulations()
    expires = datetime.now() + timedelta(seconds=24*3600) # 24 hrs
    # Allt þetta "expiry" þarf eitthvað að skoða og hugsa
    thread = threading.Thread(target=run_thread_simulation, args=(sid,))
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
        "target": sim.sim_settings["simulation_count"],
    }
    sim_results = sim.get_results_dict()
    add_vuedata(sim_results)
    #disp("sim_status", sim_status)
    if stop:
        sim.terminate = True
        # thread.join() finishes the thread and sets thread.done to True
        thread.join()
    return sim_status, sim_results

def simulation_to_excel(sid, file):
    (sim, _, _) = SIMULATIONS[sid]
    sim.to_xlsx(file)

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
    didbytes = (str(did) + ":"
                + str(random.randint(1, 100000000))).encode('utf-8')
    h.update(didbytes)
    return h.hexdigest()

SIMULATIONS = {}
SIMULATION_IDX = 0
