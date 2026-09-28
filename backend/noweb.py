import time, par_util
from threading import Thread
from par_util import write_sim_settings, write_sim_stop, read_sim_dict
from par_util import read_sim_status, read_sim_error
from electionHandler import ElectionHandler
from input_files import load_json, load_votes
from simulate import Simulation, Sim_result

def create_SIMULATIONS():
    global SIMULATIONS
    SIMULATIONS = {}

def single_election(votes, systems):
    '''obtain results from single election for specific votes and a
    list of electoral systems'''
    if isinstance(votes, str):
        raise RuntimeError(votes)
    handler = ElectionHandler(votes, systems, use_thresholds=True)
    elections = handler.elections
    results = [election.get_result_web() for election in elections]
    return results

def run_thread_simulation(simid):
    try:
        SIM = SIMULATIONS[simid]
        sim = SIM['sim']
        thread = SIM['thread']
        thread.done=False
        sim.simulate()
        thread.done = True
    except Exception as e:
        SIM['exception'] = e
        raise

def new_simulation(votes, systems, sim_settings):
    parallel = sim_settings["cpu_count"] > 1
    threaded = sim_settings["cpu_count"] == 1
    simid = par_util.get_id()
    starttime = time.time()
    SIMULATIONS[simid] = {'time':starttime, 'exception':None}
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

def fix_str_keys(dictionary_list):
    new_dictionary_list = []
    for d in dictionary_list:
        new_d = {}
        for k in d.keys():
            new_d[int(k)] = d[k]
        new_dictionary_list.append(new_d)
    return new_dictionary_list

def check_simulation(simid, stop=False):
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
            from time import sleep
            sleep(0.25)
            sim_dict = read_sim_dict(simid)
            for key in sim_dict["histogram_data"]:
                sim_dict['histogram_data'][key] = \
                    fix_str_keys(sim_dict['histogram_data'][key])
            sim_result = Sim_result(sim_dict)
            process = SIM['process']
            process.wait()
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
        sim_result_dict = sim_result.get_result_web(parallel)
        SIMULATIONS[simid]['result'] = sim_result
    else:
        sim_result_dict = {'data': []}
    return sim_status, sim_result_dict
