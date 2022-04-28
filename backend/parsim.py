from par_util import *
from util import disp, timestamp
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
    return sim.attributes()

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
    nsim = sim_settings["simulation_count"]
    nproc = min(nsim, sim_settings["cpu_count"]) # no more processes than nsim
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
        sleep(0.2)
        if read_sim_stop(simid):
            monitor.send_stopsignal()
        sim_status = get_sim_status(monitor, nsim)
        if asyncres.ready():
            sim_status["done"] = True
            break
        print(timestamp(), "(1) sim_status=", sim_status)
        write_sim_status(simid, sim_status)
    sim_dicts = asyncres.get()
    sim0 = Sim_result(sim_dicts[0])
    for i in range(1,len(sim_dicts)):
        sim_i = Sim_result(sim_dicts[i])
        sim0.combine(sim_i)
    sim0.analysis()
    del sim0.stat
    sim_dict = vars(sim0)
    write_sim_dict(simid, sim_dict)
    sleep(0.1)
    print(timestamp(), "(2) sim_status=", sim_status)
    write_sim_status(simid, sim_status) # write with done after sim_result_dict

if __name__ == "__main__":
    import sys
    simid = sys.argv[1]
    try:
        parallel_simulate(simid)
    except BrokenPipeError:
        print('Caught broken pipe error')
    except Exception:
        trace = "PARSIM ERROR:\n" + long_traceback(format_exc())
        print(trace, file=sys.stderr)
        write_sim_error(simid, trace)
        raise SystemExit('')
