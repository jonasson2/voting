#!/usr/bin/env python3
import sys
sys.path.append("../backend")
import numpy as np
import json
import sys
if "google.colab" in sys.modules:
  dir = "results/newres01a"
else:
  dir = sys.argv[1]
jsonfile = dir + "/meta.json"
histfile = dir + "/h.csv"
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

def table(system_names, A, hdr, mean, symbol=" "):
    print()
    _,ncol = np.shape(A)
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
    S = np.zeros((10,7))
    for i in range(nsys):
        for j in range(maxf):
            S[i,j] = sum(Hp[i,j:])
    table(system_names, Hp, "Number of seat changes", mean)
    table(system_names, S, "Cumulative seat changes", mean, '≥')
    
tables(system_names, H)
