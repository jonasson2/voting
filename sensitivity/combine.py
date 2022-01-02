#!/usr/bin/env python3
import sys, math
sys.path.append("../backend")
import numpy as np, json
from pathlib import Path
from util import writecsv
from run_util import get_arguments, runshell
from histogram import combine_histogram_lists, histograms2array

(cv,votes) = get_arguments(
    args = [
        ['cv',     str, 'total number of simulations'],
        ['votes',  str, 'number of cores']],
    description = "Combine simulation results from cluster run",
    epilog = (
        "Combines the histograms in mimir:~/runpar/<cv>/<votes>/{host,...}/h.csv"
        " and writes the result to local file ~/runpar/<cv>/<votes>/h.csv")
)

def combine_meta(result_folder, meta_file):
    files = runshell(f'ls {result_folder}/*/meta.json')
    n_reps = 0
    for jsonfile in files:
        with open(jsonfile) as f:
            results = json.load(f)
            n_reps += results["n_reps"]
        results["n_reps"] = n_reps
        with open(meta_file, 'w') as newf:
            json.dump(results, newf, ensure_ascii=False, indent=2)

def combine_hist():
    home = Path.home()
    result_folder = home/"runpar"/cv/votes
    result_folder.parent.mkdir(parents=True, exist_ok=True)
    runshell(f'scp -qr mimir:runpar/{cv}/{votes} {result_folder}')
    files = runshell(f'ls {result_folder}/*/h.csv')
    result_list = []
    for file in files:
        result_list.append(np.loadtxt(file, delimiter=','))
    result = combine_histogram_lists(result_list)
    result = histograms2array(result)
    return result_folder, result

(result_folder, result) = combine_hist()
meta_file = result_folder/"meta.json"
combine_meta(result_folder, meta_file)
combined_file = result_folder/"h.csv"
writecsv(combined_file, result)
print(f'Wrote combined histogram to {combined_file}')
print(f'and meta information to {meta_file}')


