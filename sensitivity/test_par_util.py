import multiprocessing as mp, sys
from time import sleep
sys.path.append("../backend")
from par_util import *
from traceback import format_exc
from trace_util import traceback

def prufa(nr, ntask, monitor):
    print(f'starting process {nr}')
    for k in range(ntask):
        sleep(0.3)
        info = k+1
        if k==1:
            pass
            #x = k/0
        stop = monitor.monitor(nr, info)
        if stop:
            print(f'worker {nr} received stopsignal')
            return None
    return 'result'
        
def main():
    simid = get_id()
    nproc = 2
    ntask = 15
    monitor = Monitor(nproc)
    p = mp.Pool(nproc)
    pars = ((nr,ntask,monitor) for nr in range(nproc))
    asyncres = p.starmap_async(prufa, pars)
    kcheck = 0
    while True:
        sleep(1)
        kcheck += 1
        if kcheck==3:
            pass
            #monitor.send_stopsignal()
        (info, runtime) = monitor.collect_progress()
        #write_sim_status(simid,info)
        print(f'info = {info}')
        if asyncres.ready():
            print('breaking')
            break
    print('simid =', simid)
    try:
        results = asyncres.get()        
        if not all(results):
            print('stopped')
        else:
            write_sim_results(simid,results)
            print('results =', results)
    except Exception:
        trace = traceback(format_exc(), 2)
        print("ERROR, traceback:")
        print(trace)

if __name__ == "__main__":
    main()
