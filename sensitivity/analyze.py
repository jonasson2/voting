#!/usr/bin/env python3
import sys, json, math, scipy.stats as stat, numpy as np
from pathlib import Path
from run_util import get_arguments, get_hostname
sys.path.append("../backend")
from util import remove_suffix

(cv, votes, local) = get_arguments(
    args=[
        ['cv',     str,  'fractional part of coefficient of variation'],
        ['votes',  str,  'stem of vote file'],
        ['-local', bool, 'use results from simulation on local host']
    ],
    description = "Analyze results from sensitivity simulation",
    epilog = ("Reads the files <dir>/{h.csv,meta.json} and prints a table with "
              "simulation results; <dir> is ~/runpar/<cv>/<votes> or, when "
              "-local is specified, ~/runpar/<cv>/<votes>/<host>")
)

dir = Path.home()/'runpar'/cv/votes
if local:
    host = get_hostname()
    dir /= host
jsonfile = dir/"meta.json"
histfile = dir/"h.csv"
with open(jsonfile) as f:
    results = json.load(f)
H = np.loadtxt(histfile, delimiter=',')
sim_settings = results["sim_settings"]
n_reps       = results["n_reps"]
system_names = results["system_names"]
vote_file    = results["vote_file"]
vote_generation_dist = sim_settings["gen_method"]
adjustment_dist      = sim_settings["sens_method"]
vote_cv              = sim_settings["distribution_parameter"]
adjust_cv            = sim_settings["sens_cv"]

print()
print(f"Vote file                      = {vote_file}")
print(f"Number of generated votes      = {n_reps}")
print(f"Number of adjustments for each = {1}")
print(f"Vote generation:")
print(f"  distribution             = {vote_generation_dist}")
print(f"  coefficient of variation = {vote_cv}")
print(f"Adjustment simulation:")
print(f"  distribution             = {adjustment_dist}")
print(f"  coefficient of variation = {adjust_cv}")
print(f"Accuracy (99%) for specific p:")
z = - stat.norm.ppf(0.005)
for p in [0.5, 0.1, 0.02, 0.005, 0.001]:
    n_reps = round(5e6)
    accuracy = z*math.sqrt(p*(1-p)/n_reps)
    print(f"  p={p*100:5.2f}%: ± {100*accuracy:.3f}%")

def table(system_names, A, hdr, mean, symbol=" ", ncol=None):
    print()
    _, ncolA = np.shape(A)
    if not ncol:
        ncol = ncolA
    else:
        ncol = min(ncol, ncolA)
    h1 = "Voting system"
    ws = max([len(h1), *(len(s) for s in system_names)])
    wm = 7
    wh = 49
    print(f"{' ':{ws+wm+3}}{hdr:–^{wh}s}")
    print(f"{h1:{ws}}  Mean  ", end='')
    for i in range(ncol):
        print(f"    {symbol}{2*i:<2}", end='')
    print()
    print("–"*(ws+wm+3+wh))
    for i in range(len(H)):
        sys = system_names[i]
        m = mean[i]
        row = A[i]
        print(f"{sys:{ws}}  {m:5.3f} ", end='')
        for j in range(ncol):
            dp = 1 if j<5 else 2
            print(f"{row[j]:{5+dp}.{dp}f}%",end='')
        print()

def tables(system_names, H):
    (nsys,n) = np.shape(H)
    hsum = np.sum(H,0)
    maxf = max(i for (i,x) in enumerate(sum(H)) if x>0)
    H = H[:,:maxf]
    f = np.arange(maxf)
    Hf = H*f    
    mean = np.sum(Hf,1)/np.sum(H,1)
    Hp = H/(np.sum(H,1).reshape(-1,1))*100
    S = np.zeros((nsys,maxf))
    for i in range(nsys):
        for j in range(maxf):
            S[i,j] = sum(Hp[i,j:])
    table(system_names, Hp, "Number of seat changes", mean, ' ', 7)
    table(system_names, S, "Cumulative seat changes", mean, '≥', 7)
    
tables(system_names, H)
