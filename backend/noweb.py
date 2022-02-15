import threading, random, os, csv, warnings, json, time, par_util
from pathlib import Path
from par_util import write_sim_settings, write_sim_stop, read_sim_results, clean
from par_util import read_sim_status
from datetime import datetime, timedelta
from electionSystem import ElectionSystem
from electionHandler import ElectionHandler, update_constituencies
from util import disp, check_votes, load_votes_from_excel
from input_util import check_input, check_systems, check_simul_settings
from simulate import Simulation, Sim_result
from dictionaries import CONSTANTS
from sim_measures import add_vuedata

# Catch NumPy warnings (e.g. zero divide):
warnings.filterwarnings('error', category=RuntimeWarning)

def load_votes(filename):
    with open(filename,"r") as f:
        reader = csv.reader(f, skipinitialspace=True)
        lines = list(reader)
    result = check_votes(lines, filename)
    return result

def load_settings(f):
    # returns systems and sim_settings from json-file f
    if isinstance(f,Path) or isinstance(f,str):
        with open(f) as file: file_content = json.load(file)
    else:
        file_content = json.load(f.stream)
    assert type(file_content) == dict
    if "e_settings" in file_content:
        file_content["systems"] = file_content["e_settings"]
        del file_content["e_settings"]
    assert "sim_settings" in file_content
    assert "systems" in file_content
    file_content["sim_settings"] = check_simul_settings(file_content["sim_settings"])
    assert type(file_content["systems"]) == list
    # keys = ["name", "seat_spec_option", "constituencies",
    #         "constituency_threshold", "constituency_allocation_rule",
    #         "adjustment_threshold", "adjustment_division_rule",
    #         "adjustment_method", "adjustment_allocation_rule"]
    # systems = []
    for item in file_content["systems"]:
        if item["adjustment_method"] == "8-nearest-neighbor":
            item["adjustment_method"] = "8-nearest-to-last"
        if "constituency_allocation_rule" in item:
            item["primary_divider"] = item["constituency_allocation_rule"]
        if "adjustment_division_rule" in item:
            item["adj_determine_divider"] = item["adjustment_division_rule"]
        if "adjustment_allocation_rule" in item:
            item["adj_alloc_divider"] = item["adjustment_allocation_rule"]
    return file_content

def single_election(votes, systems):
    '''obtain results from single election for specific votes and a
    list of electoral systems'''
    min_votes = CONSTANTS["minimum_votes"]
    elections = ElectionHandler(votes, systems, min_votes=min_votes).elections
    results = [election.get_results_dict() for election in elections]
    return results

def run_thread_simulation(simid):
    SIM = SIMULATIONS[simid]
    sim = SIM['sim']
    thread = SIM['thread']
    thread.done=False
    sim.simulate()
    thread.done = True

def new_simulation(votes, systems, sim_settings):
    global SIMULATIONS
    parallel = sim_settings["cpu_count"] > 1
    simid = par_util.get_id()
    now = time.time()
    #timestamp = time.strftime("%H:%M:%S")
    SIMULATIONS[simid] = {'time':now}
    if not parallel:
        simulation = Simulation(sim_settings, systems, votes)
        thread = threading.Thread(target=run_thread_simulation, args=(simid,))
        thread.start()
        SIMULATIONS[simid].update({'sim':simulation, 'thread':thread})
    else:
        data = {'votes':votes, 'systems':systems, 'sim_settings':sim_settings}
        write_sim_settings(simid, data)
        pid = par_util.start_python_command('parsim.py', simid)
        SIMULATIONS[simid].update({'pid':pid, 'thread':None})
    return simid

def check_simulation(simid, stop=False):
    import os, time
    if not simid in SIMULATIONS:
        raise KeyError('Simulation has stopped running')
    thread = SIMULATIONS[simid]['thread']
    parallel = thread is None
    SIMULATIONS[simid]['time'] = time.time()
    if not parallel:
        sim = SIMULATIONS[simid]['sim']
        sim_status = {
            "done": thread.done,
            "iteration": sim.iteration,
            "time_left": sim.time_left,
            "total_time": sim.total_time,
        }
        print('iteration=', sim.iteration)
        raw_result = sim.get_raw_result()
        sim_result = Sim_result(raw_result)
        sim_result.analysis()
        sim_results = sim_result.get_results_dict()
        print('data length:', len(sim_results["data"]))
        #print('stop=', stop)
        if stop:
            sim.terminate = True
            thread.join()
    else:
        if stop:
            write_sim_stop(simid)
        sim_status = read_sim_status(simid)
        if sim_status["done"]:
            sim_results = read_sim_results(simid)
            # raise RuntimeError('Results not available')
        else:
            sim_results = {'data': []}
    add_vuedata(sim_results, parallel)
    return sim_status, sim_results

def simulation_to_excel(simid, file):
    sim = SIMULATIONS[simid]["sim"]
    sim.to_xlsx(file)

SIMULATIONS = {}
SIMULATION_IDX = 0
