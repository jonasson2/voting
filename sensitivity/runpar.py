#!/usr/bin/env python3
import sys, math, time
from run_util import get_arguments, runshell, run_parallel, get_hostname
from pathlib import Path

def freenodes():
    # Returns a dictionary free with free[compute-node] giving the number of
    # free cores on each compute-node on cs.hi.is/mimir
    free = {}
    for info in runshell("freecpu"):
        (node,freestr) = info.split()
        free[node] = float(freestr)
    return free

args = get_arguments(
    args = [
        ['n_sim',    int,   'total number of simulations'],
        ['votes',    str,   'use votes from data/<votes>.csv'],
        ['-sens_cv', float, 'coefficient of variation for adjustment', 0.01],
        ['-cv',      float, 'variation coefficient for vote generation', 0.25]],
    description = "Run simulation in parallel on compute nodes",
    epilog = ("Runs sensitivity simulation with sim.py on all available "
              "cores on each compute node as given by running the shell-"
              "script freecpu. Results are written to <dir>/{h.csv,meta."
              "csv} where <dir> is ~/runpar/<cv>/<votes>/<compute-node>, "
              "and a log is written to dir/sim.log every 100 iterations"))

def runsim():
    def errorfile(node):
        return Path.home()/'runpar'/f'error-{node}.log'
    free = freenodes()
    for node in free:
        free[node] = round(free[node])
    total_cores = sum(free.values())
    print('total_cores =', total_cores)
    (n_total_sim, votes, sens_cv, cv) = args
    errorfiles = []
    for (node,cores) in free.items():
        n_sim = math.ceil(n_total_sim/total_cores*cores)
        command = f'sim.py {n_sim} {cores} {votes}'
        errorfiles.append(errorfile(node))
        pid = run_parallel(node, command, errorfiles[-1])
        print(f'{node}: {pid}, nsim={n_sim}, cores={cores}, command={command}')
    time.sleep(1)
    for file in errorfiles:
        if file.exists() and file.stat().st_size > 0:
            output = runshell(f'echo "{file.name}:"; cat {file}')
            print(*output, sep='\n  ')
        elif file.exists():
            file.unlink()

if __name__ == "__main__":
    runsim()
