#!/usr/bin/env python3
import sys
sys.path.append("../backend")
import numpy as np
import json
import sys
from util import disp, dispv

dir = sys.argv[1]
jsonfile = dir + "/meta.json"
meanfile = dir + "/m.csv"
stdfile = dir + "/s.csv"
with open(jsonfile) as f:
    results = json.load(f)
A = np.loadtxt(meanfile, delimiter=',')
S = np.loadtxt(stdfile, delimiter=',')
assert len(A) == len(S)
inner_settings = results["inner_settings"]
outer_settings = results["outer_settings"]
n_beta_sim   = len(A)
n_unif_sim   = results["n_unif_sim"]
system_names = results["system_names"]
vote_file    = results["vote_file"]
outer_dist   = outer_settings["gen_method"]
ocv          = outer_settings["distribution_parameter"]
inner_dist   = inner_settings["gen_method"]
icv          = inner_settings["distribution_parameter"]

S_mean = np.mean(S,0)
S_std = np.std(S,0)
dispv('S_mean', S_mean)
dispv('S_std', S_std)

print()
print(f"Vote file                   = {vote_file}")
print(f"Number of outer simulations = {n_beta_sim}")
print(f"Number of inner simulations = {n_unif_sim}")
print(f"Outer simulation:")
print(f"  distribution             = {outer_dist}")
print(f"  coefficient of variation = {ocv}")
print(f"Inner simulation:")
print(f"  distribution             = {inner_dist}")
print(f"  coefficient of variation = {icv}")

def table(system_names, A):
    mean = np.mean(A, axis=0)
    std = np.std(A, axis=0)
    stderr = std/np.sqrt(len(A))
    p90 = np.percentile(A, 90, axis=0) 
    p99 = np.percentile(A, 99, axis=0) 
    
    print(f"\nSeat change count with {icv*100:.1f}% change in votes:\n")
    h1 = "Voting system"
    ns = max([len(h1), *(len(s) for s in system_names)])
    print(f"{h1:{ns}}  Mean    SE     SD  90-pctile 99-pctile")
    print("–"*(ns + 3*6 + 2*11))
    for (sys,m,se,s,p,q) in zip(system_names, mean, stderr, std, p90, p99):
        print(f"{sys:{ns}}  {m:5.3f}  {se:5.3f}  {s:4.2f}   {p:4.2f}      {q:4.2f}")

table(system_names, A)
