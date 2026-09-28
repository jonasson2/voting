from par_util import *
from util import disp, timestamp, hms
from simulation_chunks import combine_chunks, run_chunk, split_replicates
import multiprocessing as mp
from time import time, sleep
from trace_util import traceback, long_traceback
def task_simulate(nr, ntask, start_iteration, sim_settings, systems, votes, monitor):
    return run_chunk(votes, systems, sim_settings, ntask, start_iteration,
                     nr=nr, monitor=monitor)

def get_status(monitor, nsim):
    # GET CURRENT STATUS FROM THE WORKERS
    (info, runtime, stopped) = monitor.collect_progress()
    iterations = sum(info.values())
    time_left = runtime/iterations*(nsim - iterations) if iterations else 0
    done = iterations >= nsim or monitor.has_stopped()
    sim_status = {
        "iteration": iterations,
        "time_left": hms(time_left),
        "total_time": hms(runtime),
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
    chunks = split_replicates(nsim, sim_settings["cpu_count"])
    nproc = len(chunks)
    monitor = Monitor(nproc)
    starttime = time()

    # CREATE POOL OF WORKERS
    pars = ((index, count, start, sim_settings, systems, votes, monitor)
            for index, (count, start) in enumerate(chunks))
    pool = mp.Pool(nproc)

    # START THE WORKERS
    asyncres = pool.starmap_async(task_simulate, pars)

    # CHECK FOR STATUS REGULARLY AND WRITE TO DISK
    while True:
        sleep(0.2)
        if read_sim_stop(simid):
            monitor.send_stopsignal()
        sim_status = get_status(monitor, nsim)
        if asyncres.ready():
            sim_status["done"] = True
            break
        #print(timestamp(), "(1) sim_status=", sim_status)
        write_sim_status(simid, sim_status)
    sim_dicts = asyncres.get()
    sim0 = combine_chunks(sim_dicts)
    del sim0.stat
    sim_dict = vars(sim0)
    write_sim_dict(simid, sim_dict)
    sleep(0.1)
    #print(timestamp(), "(2) sim_status=", sim_status)
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
