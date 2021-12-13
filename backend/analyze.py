#!/usr/bin/env python3
import numpy as np
import json
import sys
from util import disp, dispv

result_filename = sys.argv[1]
with open(result_filename) as jsonfile:
    results = json.load(jsonfile)
A = results["mean_alloc_diff"]
S = results["std_alloc_diff"]
n_beta_sim = results["n_beta_sim"]
A = np.array(A)
S = np.array(S)
A_mean = np.mean(A,0)
A_std = np.std(A,0)
S_mean = np.mean(S,0)
S_std = np.std(S,0)
A_stderr = S_mean/np.sqrt(n_beta_sim)
dispv('A',A)
dispv('S',S)
dispv('A_mean', A_mean)
dispv('S_mean', S_mean)
dispv('A_stderr', A_stderr)

