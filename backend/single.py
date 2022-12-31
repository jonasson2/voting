#!/usr/bin/env python3
import sys, math, time, random
from run_util import get_arguments, get_hostname
sys.path.append("../backend")
from electionHandler import ElectionHandler
from noweb import load_votes, load_json, single_election, votes_to_excel
from copy import deepcopy, copy
import json
from util import disp, dispv, remove_suffix, hms, writecsv
from pathlib import Path
from dictionaries import ADJUSTMENT_METHODS
from method_abbrev import method_dicts_land
from numpy import flatnonzero as find
from electionSystem import ElectionSystem
#sys_file = "default-rule.json"
#sys_file = "2reglur.json"
defaultmethod = 'votepct'

def read_data(vote_file, json_file_or_method):
    JSONFILE = json_file_or_method.endswith('.json')
    data = Path('data')
    if JSONFILE:
        json_file = Path(json_file_or_method).expanduser()
        if json_file.parent.samefile('.'):
            json_file = data/json_file
        jsondata = load_json(json_file)
        systems = jsondata["systems"]
    else:
        abbrev = json_file_or_method
        method_name = next(x['long'] for x in method_dicts_land if x['short'] == abbrev)
        method = ADJUSTMENT_METHODS[method_name]
        system = ElectionSystem()
        system["adjustment_method"] = method_name
    if not vote_file and JSONFILE and "vote_table" in jsondata:
        votes = jsondata["vote_table"]
        vote_path = Path(json_file) # for reporting in metadata
    else:
        if not vote_file:
            print('No votes specified, using "typical 21st century"')
            vote_file = 'icel-21st-c.csv'
        vote_path = Path(vote_file).expanduser()
        if vote_path.parent.samefile('.'):
            vote_path = data/vote_path
        if vote_file.endswith('.json'):
            votes = load_json(vote_file)["vote_table"]
        else:
            votes = load_votes(vote_path)
    if not JSONFILE:
        system.copy_info_from_votes(votes)
        systems = [system]
    return votes, vote_path, systems

def main():
    (json_file_or_method, vote_file) = get_arguments(
        args=[
            ['json_file|method', str, ('json file with settings and possibly votes,\n'
                                       'or name of method (requires -v)'),
             defaultmethod],
            ['-vote', str, 'specify vote file', None, 'file']],
        description=("Compute results for a single election, methods can be one of:\n"
                    "   party1st   relmarg    relsup      switch\n"
                    "   land1st    absmarg    relsupsmp   optimal\n"
                    "   votepct    nearprev   relsupmed   gurobi\n"
                    "   seatsh "))
    (votes, vote_path, systems) = read_data(vote_file, json_file_or_method)

    #random.seed(42)
    results = single_election(votes, systems)
    handler = ElectionHandler(votes, systems, use_thresholds=True)
    handler.to_xlsx("single.xlsx")
    votes_to_excel(votes, "votes.xlsx")

    disp(results, title='results')

if __name__ == "__main__":
    main()
