#!/usr/bin/env python3
import sys, math, time, random
from run_util import get_arguments, get_hostname
sys.path.append("../backend")
from electionHandler import ElectionHandler
from noweb import load_votes, load_json, single_election, votes_to_excel
from histogram import combine_histograms, combine_histogram_lists, histograms2array
from copy import deepcopy, copy
import json
from util import disp, dispv, remove_suffix, hms, writecsv
from pathlib import Path

#sys_file = "default-rule.json"
#sys_file = "2reglur.json"
defaultfile = 'switching.json'

def read_data(vote_file, json_file):
    json_file = Path(json_file).expanduser()
    data = Path('data')
    if json_file.parent.samefile('.'):
        json_file = data/json_file
    jsondata = load_json(json_file)
    systems = jsondata["systems"]
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
    return votes, vote_path, systems

def main():
    (json_file, vote_file) = get_arguments(
        args=[
            ['json_file', str, 'json file with settings and possibly votes', defaultfile],
            ['-votes', str, 'specify vote file', '']],
        description="Compute results for a single election")
    (votes, vote_path, systems) = read_data(vote_file, json_file)

    #random.seed(42)
    systemnames = [s["name"] for s in systems]        # self.test_generated() --- needs to be rewritten,
        # (statistical test of simulated data)


    results = single_election(votes, systems)
    handler = ElectionHandler(votes, systems)
    handler.to_xlsx("single.xlsx")
    votes_to_excel(votes, "votes.xlsx")

    print('results=', results)

if __name__ == "__main__":
    main()
