#!/usr/bin/env python3
import sys, math, time, random
from run_util import get_arguments, get_hostname
sys.path.append("../backend")
from multiprocessing import Pool
from noweb import load_votes
from noweb import load_json
from noweb import single_election
from noweb import start_simulation, check_simulation, run_simulation, SIMULATIONS
from histogram import combine_histograms, combine_histogram_lists, histograms2array
from copy import deepcopy, copy
import json
from util import disp, dispv, remove_suffix, hms, writecsv
from pathlib import Path

#sys_file = "default-rule.json"
#sys_file = "2reglur.json"
data = Path('data')
defaultfile = '10kerfi-aldarkosning.json'

(n_reps, n_cores, json_file, vote_file, sens_cv, cv) = get_arguments(
    args = [
        ['n_reps',   int,   'total number of simulations',                10          ],
        ['n_cores',  int,   'number of cores',                            1           ],
        ['json_file',str,   'json file with settings and possibly votes', defaultfile ],
        ['-votes',   str,   'vote file',                                  ''          ],
        ['-sens_cv', float, 'coefficient of variation for adjustment',   0.01         ],
        ['-cv',      float, 'variation coefficient for vote generation', 0.25        ]],
    description="Simulate sensitivity of elections")

def read_data():
    global vote_file, json_file
    json_file = Path(json_file).expanduser()
    if json_file.parent.samefile('.'):
        json_file = data/json_file
    jsondata = load_json(json_file)
    systems = jsondata["systems"]
    sim_settings = jsondata["sim_settings"]
    if not vote_file:
        if "vote_table" in jsondata:
            votes = jsondata["vote_table"]
            vote_file = json_file # for reporting in metadata
        else:
            print('No votes specified, using "typical 21st century"')
            vote_file = 'icel-21st-c.csv'
    vote_file = Path(vote_file).expanduser()
    if vote_file.parent.samefile('.'):
        vote_file = data/vote_file
    votes = load_votes(vote_file)
    return votes, systems, sim_settings

def set_sim_settings(sim_settings, n_sim, sens_cv, cv):
    settings = deepcopy(sim_settings)
    settings["simulation_count"] = n_sim
    settings["distribution_parameter"] = cv
    settings["sens_cv"] = sens_cv
    settings["sensitivity"] = True
    return settings

def filenames(sens_cv, n_cores, n_sim):
    from datetime import datetime
    host = get_hostname()
    fraccv = f'{sens_cv}'[2:]
    now = datetime.now().strftime('%Y.%m.%dT%H.%M')
    votestem = vote_file.stem
    folder = Path.home() / 'runpar' / fraccv / votestem / host
    folder.mkdir(parents=True, exist_ok=True)
    metadatafile = folder / "meta.json"
    histfile = folder / "h.csv"
    logfile = folder / "sim.log"
    with open(logfile, 'w') as logf:
        def log(s): print(s, file=logf)
        log(f'Host:          {host}')
        log(f'Votes:         {votestem}')
        log(f'Adjust-CV:     {sens_cv}')
        log(f'Time:          {now}')
        log(f'n_cores:       {n_cores}')
        log(f'reps per core: {n_sim}')
    return metadatafile, histfile, logfile

(votes, systems, sim_settings) = read_data()
n_sim = math.ceil(n_reps/n_cores)
sim_settings = set_sim_settings(sim_settings, n_sim, sens_cv, cv)
(metadatafile, histfile, logfile) = filenames(sens_cv, n_cores, n_sim)

def main():
    random.seed(42)
    systemnames = [s["name"] for s in systems]
    pars = range(n_cores)
    if sim_settings['simulation_count'] == 0: return
    sim_settings["sensitivity"] = False
    beginning_time = time.time()
    if n_cores > 1:
        p = Pool(n_cores)
        results = p.map(simulate, pars)
    else:
        pass
        results = [simulate(0)]
    if sim_settings["sensitivity"]:
        hist = combine_histogram_lists(results)
        hist_array = histograms2array(hist)

        metadata = {
            "n_reps":        n_reps,
            "vote_file":     str(vote_file),
            "system_names":  systemnames,
            "sim_settings":  sim_settings,
        }
        with open(metadatafile, 'w', encoding='utf-8') as fd:
            json.dump(metadata, fd, ensure_ascii=False, indent=2)
        print(histfile)
        writecsv(histfile, hist_array)
    else:
        disp('results', results)
    elapsed_time = hms(time.time() - beginning_time)
    with open(logfile, 'a') as logf:
        for f in logf, sys.stdout:
            print(f'Simulation finished, elapsed time: {elapsed_time}', file=f)

def simulate(idx):
    logfile0 = logfile if idx == 0 else None
    result = run_simulation(votes, systems, sim_settings, logfile=logfile0)
    if sim_settings["sensitivity"]:
        list_sens,_ = result
        return list_sens
    else:
        return result


print("name=",__name__)
if __name__ == "__main__":
    main()
