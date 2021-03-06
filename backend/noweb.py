import random, os, csv, json, time, par_util, sys
from threading import Thread, excepthook
from pathlib import Path
from par_util import write_sim_settings, write_sim_stop, read_sim_dict, clean
from par_util import read_sim_status, read_sim_error, parallel_dir
from datetime import datetime, timedelta
from electionSystem import ElectionSystem
from electionHandler import ElectionHandler, update_constituencies
from util import disp, check_votes, load_votes_from_excel
from input_util import check_input, check_systems, check_simul_settings
from simulate import Simulation, Sim_result
from dictionaries import CONSTANTS
from excel_util import simulation_to_xlsx, votes_to_xlsx
import psutil

def create_SIMULATIONS():
    global SIMULATIONS
    SIMULATIONS = {}

def load_votes(filename):
    with open(filename,"r") as f:
        reader = csv.reader(f, skipinitialspace=True)
        lines = list(reader)
    result = check_votes(lines, filename)
    return result

def correct_deprecated(L):
    # Remove 1-, 2- etc. from deprecated values in L["systems"]
    import re
    deprec_list = [
        "adj_alloc_divider",          "adj_determine_divider",
        "adjustment_allocation_rule", "adjustment_division_rule",
        "adjustment_method",          "constituency_allocation_rule",
        "name",                       "primary_divider"]
    old_names = {
        "norwegian-icelandic": "max-const-seat-share",
        "pure-vote-ratios":    "max-const-vote-percentage",
        "nearest-neighbor":    "nearest-to-previous",
        "nearest-to-last":     "nearest-to-previous",
    }
    translate = {
        "constituency_allocation_rule": "primary_divider",
        "adjustment_division_rule":     "adj_determine_divider",
        "adjustment_allocation_rule":   "adj_alloc_divider",
    }
    for deprec in deprec_list:
        for sys in L["systems"]:
            if deprec in sys:
                sys[deprec] = re.sub('^[0-9AB]-', '', sys[deprec])
        
        if "constituency_allocation_rule" in sys:
            sys["primary_divider"] = sys["constituency_allocation_rule"]
        if "adjustment_division_rule" in sys:
            sys["adj_determine_divider"] = sys["adjustment_division_rule"]
        if "adjustment_allocation_rule" in sys:
            sys["adj_alloc_divider"] = sys["adjustment_allocation_rule"]
    for sys in L["systems"]:
        for (old,new) in old_names.items():
            if sys["adjustment_method"] == old:
                sys["adjustment_method"] = new
        for (oldkey, newkey) in translate.items():
            if oldkey in sys:
                sys[oldkey] = sys[newkey]
    return L

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
    file_content = correct_deprecated(file_content)
    return file_content

def single_election(votes, systems):
    '''obtain results from single election for specific votes and a
    list of electoral systems'''
    min_votes = CONSTANTS["minimum_votes"]
    handler = ElectionHandler(votes, systems, min_votes=min_votes)
    elections = handler.elections
    results = [election.get_result_dict() for election in elections]
    return results

def run_thread_simulation(simid):
    try:
        global SIMULATIONS
        SIM = SIMULATIONS[simid]
        sim = SIM['sim']
        thread = SIM['thread']
        thread.done=False
        sim.simulate()
        thread.done = True
    except Exception as e:
        print('[zer] caught exception')
        SIM['exception'] = e
        raise Exception(e)

def new_simulation(votes, systems, sim_settings):
    global SIMULATIONS
    terminate_old_simulations(maxminutes = 0.5)
    parallel = sim_settings["cpu_count"] > 1
    threaded = sim_settings["cpu_count"] == 1
    simid = par_util.get_id()
    starttime = time.time()
    SIMULATIONS[simid] = {'time':starttime, 'exception':None}
    # threaded = False
    if threaded:
        sim = Simulation(sim_settings, systems, votes)
        thread = Thread(target=run_thread_simulation, args=(simid,))
        SIMULATIONS[simid] |= {'kind':'threaded', 'sim':sim, 'thread':thread}
        thread.start()
    elif parallel:
        data = {'votes':votes, 'systems':systems, 'sim_settings':sim_settings}
        write_sim_settings(simid, data)
        process = par_util.start_python_command('parsim.py', simid)
        SIMULATIONS[simid] |= {'kind':'parallel', 'process':process}
    else: # used for debugging
        sim = Simulation(sim_settings, systems, votes)
        sim.simulate()
        SIMULATIONS[simid] |= {'kind':'sequential', 'sim':sim}
    return simid

def get_sim_status(done, sim):
    sim_status = {
        "done":       done,
        "iteration":  sim.iteration,
        "time_left":  sim.time_left,
        "total_time": sim.total_time,
    }
    return sim_status

def check_simulation(simid, stop=False):
    global SIMULATIONS
    import os, time
    if not simid in SIMULATIONS:
        raise KeyError('Simulation has stopped running')
    SIM = SIMULATIONS[simid]
    checktime = time.time()
    SIM['time'] = checktime
    kind = SIM['kind']
    if kind == 'threaded':
        thread = SIM['thread']
        if SIM['exception']:
            thread.join()
            raise SIM['exception']
        sim = SIM['sim']
        if not hasattr(thread, 'done'):
            thread.done = False
        sim_status = get_sim_status(thread.done, sim)
        sim_result = Sim_result(sim.attributes())
        sim_result.analysis()
        if stop:
            sim.terminate = True
            thread.join()
    elif kind == 'parallel':
        message = read_sim_error(simid)
        if message:
            message = '; '.join(message.split('\n'))
            raise RuntimeError(message)
        if stop:
            write_sim_stop(simid)
        sim_status = read_sim_status(simid)
        if not sim_status:
            sim_status = {
                'done':False, 'iteration':0, 'time_left':0, 'total_time':0}
        if sim_status["done"]:
            sim_dict = read_sim_dict(simid)
            sim_result = Sim_result(sim_dict)
            process = SIM['process']
            process.wait()
            #delete_tempfiles(simid)
        else:
            sim_result = None
            # raise RuntimeError('Results not available')
    else: # kind == 'sequential'; used for debugging
        sim = SIM['sim']
        sim_status = get_sim_status(True, sim)
        sim_dict = sim.attributes()
        sim_result = Sim_result(sim_dict)
        sim_result.analysis()
    if sim_result:
        parallel = kind=='parallel'
        sim_result_dict = sim_result.get_result_dict(parallel)
        SIMULATIONS[simid]['result'] = sim_result
    else:
        sim_result_dict = {'data': []}
    return sim_status, sim_result_dict

def simulation_to_excel(simid, file):
    sim_result = SIMULATIONS[simid]["result"]
    parallel = SIMULATIONS[simid]["kind"] == 'parallel'
    sim_result_dict = sim_result.get_result_dict(parallel)
    simulation_to_xlsx(sim_result_dict, file, parallel)

def votes_to_excel(vote_table, file):
    file_matrix = [
        [vote_table["name"], "cons", "adj"] + vote_table["parties"],
    ] + [
        [
            vote_table["constituencies"][c]["name"],
            vote_table["constituencies"][c]["num_const_seats"],
            vote_table["constituencies"][c]["num_adj_seats"],
        ] + vote_table["votes"][c]
            for c in range(len(vote_table["constituencies"]))
    ]
    votes_to_xlsx(file_matrix, file)    
    
def delete_tempfiles(simid):
    pardir = parallel_dir()
    for p in pardir.glob(f"{simid}*.*"):
        p.unlink()
    
def terminate_old_simulations(maxminutes):
    return # TODO: Fix this
    for (simid,sim) in SIMULATIONS.items():
        if time.time() - sim["time"] > maxminutes*60:
            print(f'simid:{simid}')
            if sim["kind"] == 'parallel':                
                process = sim["process"]
                try:
                    print(f'Stopping children of process {process.pid}...')

                    parent = psutil.Process(process.pid)
                    for child in parent.children(recursive=True):
                        child.kill()
                    parent.kill()
                    print('Wait for parent process...')
                    try:
                        process.wait()
                    except Exception as e:
                        print(f'Exception: {e}')
                    pardir = parallel_dir()
                    print(f'Removing temporary files {simid}...')
                    #delete_tempfiles(simid)
                except psutil.NoSuchProcess:
                    pass
            elif sim["kind"] == 'threaded':
                print('Terminate threaded simulation')
                sim.terminate = True
                sim['thread'].join()
    
#SIMULATIONS = {}
