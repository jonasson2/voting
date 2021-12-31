#!/usr/bin/env python3
import sys, math
from subprocess import run, Popen, PIPE
from run_util import get_arguments

def freenodes():
    # Returns a dictionary free with free[compute-node] giving the number of
    # free cores on each compute-node on cs.hi.is/mimir
    free = {}
    for info in run("freecpu", stdout=PIPE).stdout.decode().splitlines():
        (node,freestr) = info.split()
        free[node] = float(freestr)
    return free

args = get_arguments(
    args = [
        ['n_sim',    str,   'total number of simulations'],
        ['votes',    str,   'use votes from data/<votes>.csv'],
        ['-sens_cv', float, 'coefficient of variation for adjustment', 0.01],
        ['-cv'       float, 'variation coefficient for vote generation', 0.25]]  
    description = "Run simulation in parallel on compute nodes",
    epilog = ("Runs sensitivity simulation with sim.py on all available "
              "cores on each compute node as given by running the shell-"
              "script freecpu. Results are written to <dir>/{h.csv,meta."
              "csv} where <dir> is ~/runpar/<cv>/<votes>/<compute-node>, "
              "and a log is written to dir/sim.log every 100 iterations"))

def runsim():
    free = freenodes()
    total_cores = sum(free.values())
    print('total_cores =', total_cores)
    (n_total_sim, votes, sens_cv, cv) = args

    for (node,cores) in free.items():
        cores = round(cores)
        n_sim = math.ceil(n_total_sim/total_cores*cores)
        command = f'sim.py {n_sim} {cores}'
        pid = run_parallel(node, command)
        print(f'{node}: {pid}, nsim={n_sim}, cores={cores}, command={command}')

if __name__ == "__main__":
    runsim()
