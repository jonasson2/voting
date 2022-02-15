from par_util import *
from util import disp
from simulate import Simulation, Sim_result
from copy import copy
import multiprocessing as mp
from time import time, sleep
from trace_util import traceback, long_traceback

def task_simulate(nr, ntask, sim_settings, systems, votes, monitor):
    sim_settings = copy(sim_settings)
    sim_settings["simulation_count"] = ntask
    sim = Simulation(sim_settings, systems, votes, nr)
    sim.simulate(nr, monitor)
    raw_result = sim.get_raw_result()
    return raw_result

def get_sim_status(monitor, nsim):
    # GET CURRENT STATUS FROM THE WORKERS
    (info, runtime, stopped) = monitor.collect_progress()
    iterations = sum(info.values())
    time_left = runtime/iterations*(nsim - iterations) if iterations else 0
    done = iterations >= nsim or monitor.has_stopped()
    sim_status = {
        "iteration": iterations,
        "time_left": time_left,
        "total_time": runtime,
        "target": nsim,
        "done": done
    }
    return sim_status

def parallel_simulate(simid):
    # INITIALIZE
    data = read_sim_settings(simid)
    sim_settings = data["sim_settings"]
    if sim_settings["simulation_count"] == 0:
        return None
    votes = data["votes"]
    systems = data["systems"]    
    nproc = sim_settings["cpu_count"]
    nsim = sim_settings["simulation_count"]
    monitor = Monitor(nproc)
    ntask = [nsim//nproc + (1 if i < nsim % nproc else 0) for i in range(nproc)]
    starttime = time()

    # CREATE POOL OF WORKERS
    pars = ((k, ntask[k], sim_settings, systems, votes, monitor)
            for k in range(nproc))
    pool = mp.Pool(nproc)

    # START THE WORKERS
    asyncres = pool.starmap_async(task_simulate, pars)

    # CHECK FOR STATUS REGULARLY AND WRITE TO DISK
    while True:
        sleep(0.25)
        if read_sim_stop(simid):
            monitor.send_stopsignal()
        sim_status = get_sim_status(monitor, nsim)
        if asyncres.ready():
            sim_status["done"] = True
            break
        write_sim_status(simid, sim_status)
    raw_results = asyncres.get()
    sim0 = Sim_result(raw_results[0])
    for i in range(1,len(raw_results)):
        sim_result = Sim_result(raw_results[i])
        sim0.combine(sim_result)
    sim0.analysis()
    sim_results = sim0.get_results_dict()
    write_sim_results(simid, sim_results)
    write_sim_status(simid, sim_status) # write with done after sim_results

if __name__ == "__main__":
    import sys
    simid = sys.argv[1]
    try:
        parallel_simulate(simid)
    except:
        trace = "PARSIM ERROR:\n" + long_traceback(format_exc())
        print(trace, file=sys.stderr)
        raise SystemExit('')
