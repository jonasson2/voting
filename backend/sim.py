#!/usr/bin/env python3
import sys, math, time, random
from run_util import get_arguments, get_hostname
sys.path.append("../backend")
from noweb import load_votes, new_simulation
from noweb import load_json
from noweb import simulation_to_excel, simulation_plot
from noweb import check_simulation, create_SIMULATIONS
from histogram import combine_histograms, combine_histogram_lists, histograms2array
from copy import deepcopy, copy
import json
from util import disp, dispv, remove_suffix, hms, writecsv
from pathlib import Path

#sys_file = "default-rule.json"
#sys_file = "2reglur.json"
defaultfile = 'SmadæmiAlltInn.json'

def read_data(vote_file, json_file):
    json_file = Path(json_file).expanduser()
    data = Path('data')
    if json_file.parent.samefile('.'):
        json_file = data/json_file
    jsondata = load_json(json_file)
    systems = jsondata["systems"]
    sim_settings = jsondata["sim_settings"]
    if not vote_file and "vote_table" in jsondata:
        votes = jsondata["vote_table"]
        vote_path = Path(json_file) # for reporting in metadata
    else:
        if not vote_file:
            print('No votes specified, using "typical 21st century"')
            vote_file = 'icel-21st-c.csv'
        vote_path = Path(vote_file).expanduser()
        if vote_path.parent.samefile('.'):
            vote_path = data/vote_path
        votes = load_votes(vote_path)
    return votes, vote_path, systems, sim_settings

def set_sim_settings(sim_settings, n_sim, n_cpu, sens_cv, cv, pcv):
    settings = deepcopy(sim_settings)
    settings["simulation_count"] = n_sim
    settings["cpu_count"] = n_cpu
    settings["const_cov"] = cv
    settings["party_vote_cov"] = pcv
    settings["sens_cv"] = sens_cv
    settings["sensitivity"] = True
    return settings

def filenames(sens_cv, n_cores, n_sim, vote_path):
    from datetime import datetime
    host = get_hostname()
    fraccv = f'{sens_cv}'[2:]
    now = datetime.now().strftime('%Y.%m.%dT%H.%M')
    votestem = vote_path.stem
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

def main():
    create_SIMULATIONS()
    (n_reps, n_cores, json_file, vote_file, Stop, sens_cv, cv, pcv) = get_arguments(
        args=[
            ['n_reps', int, 'total number of simulations', 10],
            ['n_cores', int, 'number of cores', 1],
            ['json_file', str, 'json file with settings and possibly votes', defaultfile],
            ['-votes', str, 'vote file', ''],
            ['-Stop', int, 'stop after specified time (in seconds)', -1],
            ['-sens_cv', float, 'coefficient of variation for adjustment', 0.01],
            ['-cv', float, 'variation coefficient for vote generation', 0.3],
            ['-pcv', float, 'variation coefficient for party vote generation', 0.1]],
    description="Simulate sensitivity of elections")
    (votes, vote_path, systems, sim_settings) = read_data(vote_file, json_file)
    sim_settings = set_sim_settings(sim_settings, n_reps, n_cores, sens_cv, cv, pcv)
    (metadatafile, histfile, logfile) = filenames(sens_cv, n_cores, n_reps, vote_path)

    random.seed(43)
    systemnames = [s["name"] for s in systems]
    if sim_settings['simulation_count'] == 0: return
    sim_settings["sensitivity"] = False
    beginning_time = time.time()
    simid = new_simulation(votes, systems, sim_settings)
    stopped = False
    while True:
        time.sleep(0.25)
        stop = Stop > 0 and not stopped and time.time() > beginning_time + Stop
        if stop:
            stopped = True
        sim_status, results = check_simulation(simid, stop)
        if sim_status["done"]:
            break
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
        pass
    elapsed_time = hms(time.time() - beginning_time)
    simulation_to_excel(simid,'sim.xlsx')
    #simulation_plot(simid)
    with open(logfile, 'a') as logf:
        for f in logf, sys.stdout:
            print(f'Simulation finished, elapsed time: {elapsed_time}', file=f)

print("name=",__name__)
if __name__ == "__main__":
    main()
