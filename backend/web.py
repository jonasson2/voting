import os, tempfile, json, csv
from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from io import StringIO
from traceback import format_exc
from multiprocessing import Pool

import dictionaries, simulate
from electionSystem import ElectionSystem
from electionHandler import ElectionHandler, update_constituencies
from input_util import check_input, check_systems
from input_util import check_simul_settings
from util import disp, get_cpu_counts
from util import timestamp, timestampmsg
from trace_util import short_traceback
from noweb import load_votes, load_json, single_election
from noweb import new_simulation, check_simulation
from noweb import simulation_to_excel, votes_to_excel, create_SIMULATIONS

def errormsg(message = None):
    if not message:
        message = short_traceback(format_exc())
    return jsonify({'error': message})

class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        block_start_string='<%',
        block_end_string='%>',
        variable_start_string='%%',
        variable_end_string='%%',
        comment_start_string='<#',
        comment_end_string='#>',
    ))

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = CustomFlask('voting',
            template_folder=os.path.abspath('../vue-frontend/'),
            static_folder=os.path.abspath('../vue-frontend/static/'))

CORS(app)

@app.route('/')
def serve_index():
    digoce = os.environ.get("FLASK_DIGITAL_OCEAN", "") == "True"
    indexfile = "index-digital-ocean.html" if digoce else "index.html"
    #indexfile = "index.html"
    return render_template(indexfile)

def save_file(tmpfilename, download_name):
    import mimetypes
    (mimetype, encoding) = mimetypes.guess_type(download_name)
    response = send_from_directory(
        directory=os.path.dirname(tmpfilename),
        path=os.path.basename(tmpfilename),
        download_name=download_name,
        mimetype=mimetype,
        as_attachment=False
    )
    return response

def getparam(*args):
    data = request.get_json(force=True)
    parameters = (data[a] for a in args)
    return parameters if len(args) > 1 else next(parameters)

def getfileparam():
    return request.files["file"]

@app.route('/api/election/', methods=["POST"])
def api_election():
    try:
        (vote_table, systems) = getparam('vote_table', 'systems')
        [constituencies, nat_seats] = update_constituencies(vote_table, systems)
        for (c,n,s) in zip(constituencies, nat_seats, systems):
            s["constituencies"] = c
            s["nat_seats"] = n
        results = single_election(vote_table, systems);
        return jsonify({"results": results, "systems": systems})
    except Exception:
        return errormsg()

@app.route('/api/election/save/', methods=['POST'])
def api_election_save():
    try:
        (vote_table, systems) = getparam('vote_table', 'systems')
        handler = ElectionHandler(vote_table, systems, use_thresholds=True)
        tmpfilename = tempfile.mktemp(prefix='election-')
        handler.to_xlsx(tmpfilename)
        date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
        download_name=f"Election-{date}.xlsx"
        return save_file(tmpfilename, download_name)
    except Exception:
        return errormsg()

@app.route('/api/settings/update_constituencies/', methods=["POST"])
def api_update_constituencies():
    # Update constituencies in electoral systems according to
    # the current vote table and systems[:]["seat_spec_options"]
    try:
        (vote_table, systems) = getparam('vote_table', 'systems')
        [constituencies, nat_seats] = update_constituencies(vote_table, systems)
        return jsonify({"constituencies": constituencies, "nat_seats":nat_seats})
    except Exception:
        return errormsg()

@app.route('/api/settings/save/', methods=['POST'])
def api_settings_save():
    try:
        (systems, sim_settings) = getparam("systems", "sim_settings")
        keys = [
            "name", "seat_spec_options", "constituencies",
            "compare_with",
            "constituency_threshold", #"constituency_allocation_rule",
            "adjustment_threshold", #"adjustment_division_rule",
            "adjustment_method", #"adjustment_allocation_rule"
        ]
        names = []
        electoral_system_list = []
        for system in systems:
            names.append(system["name"])
            item = {key: system[key] for key in keys}
            item["constituency_allocation_rule"] = system["primary_divider"]
            item["adjustment_division_rule"] = system["adj_determine_divider"]
            item["adjustment_allocation_rule"] = system["adj_alloc_divider"]
            electoral_system_list.append(item)
        file_content = {
            "e_settings": electoral_system_list,
            "sim_settings": check_simul_settings(sim_settings)
        }
        tmpfilename = tempfile.mktemp(prefix='e_settings-')
        with open(tmpfilename, 'w', encoding='utf-8') as jsonfile:
            json.dump(file_content, jsonfile, ensure_ascii=False, indent=2)
        filename = secure_filename(".".join(names))
        date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
        download_filename=f"{filename}-{date}.json"
        return save_file(tmpfilename, download_filename)
    except Exception:
        return errormsg()

@app.route('/api/settings/upload/', methods=['POST'])
def api_settings_upload():
    try:
        f = getfileparam()
        settings = load_json(f)
        if "vote_table" in settings:
            return errormsg(f'File {f.filename} contains votes and must '
                            'be uploaded with "Load all"')
        return jsonify(settings)
    except Exception as e:
        if type(e).__name__ == "JSONDecodeError":
            return errormsg(f'Illegal settings file: {f.filename}')
        else:
            return errormsg()

@app.route('/api/saveall/', methods=['POST'])
def api_votes_save_all():
    try:
        param_list = ("vote_table", "systems", "sim_settings")
        param = getparam(*param_list)
        contents = dict(zip(param_list, param))
        tmpfilename = tempfile.mktemp(prefix='simulator-')
        with open(tmpfilename, 'w', encoding='utf-8') as jsonfile:
            json.dump(contents, jsonfile, ensure_ascii=False, indent=2)
        date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
        download_filename = "simulator-" + date + ".json"
        return save_file(tmpfilename, download_filename)
    except Exception:
        return errormsg()

@app.route('/api/uploadall/', methods=['POST'])
def api_votes_uploadall():
    try:
        f = getfileparam()
        content = load_json(f)
        if set(content) == {"systems", "sim_settings"}:
            return errormsg(f'File {f.filename} contains no votes and must '
                            'be uploaded with "Load from file"')
        elif set(content) == {"systems", "sim_settings", "vote_table"}:
            return jsonify(content)
        else:
            return errormsg(f'Not a legal json-file for "Load all"')
    except Exception:
        return errormsg()

@app.route('/api/votes/save/', methods=['POST'])
def api_votes_save():
    try:
        vote_table = getparam("vote_table")
        tmpfilename = tempfile.mktemp(prefix='vote_table-')
        votes_to_excel(vote_table, tmpfilename)
        download_name = secure_filename(vote_table['name']) + ".xlsx"
        return save_file(tmpfilename, download_name);
    except Exception:
        return errormsg()

@app.route('/api/presets/load/', methods=['POST'])
def api_presets_load():
    try:
        presets_dict = get_presets_dict()
        election_id = getparam('election_id')
        preset_ids = list(range(len(presets_dict)))
        if election_id not in preset_ids:
            raise ValueError("Unexpected missing ID in presets_dict")
        idx = election_id
        preset = presets_dict[idx]
        name = f'{preset["Country"]}-{preset["Name"]}-{preset["Year"]}'
        #print('name=', name)
        filename = "../data/" + presets_dict[idx]['filename']
        result = load_votes(filename)
        result["name"] = name
        return jsonify(result)
    except Exception:
        return errormsg()

@app.route('/api/votes/upload/', methods=['POST'])
def api_votes_upload():
    try:
        stream = getfileparam()
        filename = stream.filename
        result = load_votes(filename, stream)
        if isinstance(result, str):
            return errormsg(f"Illegal vote file: {result}")
        else:
            return jsonify(result)
    except Exception:
        return errormsg()

@app.route('/api/simulate/', methods=['POST'])
def api_simulate():
    try:
        (votes, systems, sim_settings) = getparam("vote_table", "systems",
                                                  "sim_settings")
        if sim_settings["simulation_count"] <= 0:
            raise ValueError("Number of simulations must be positive")
        simid = new_simulation(votes, systems, sim_settings)
        #print(f"{timestamp()}: started simulation {simid}")
        return jsonify({"started": True, "simid": simid})
    except ValueError as e:
        return errormsg(f"Error: {e}")
    except Exception:
        return errormsg()

@app.route('/api/simulate/check/', methods=['POST'])
def api_simulate_check():
    try:
        (simid,stop) = getparam("simid", "stop")
        #print(f"{timestamp()}: checking simulation {simid[:5]}")
        (status, results) = check_simulation(simid, stop)
        if status['done'] and not results:
            raise RuntimeError('Results unavailable')
        #print(f"{timestamp()}: checked simulation {simid[:5]}, status: {status}")
        return jsonify({"status": status, "results": results})
    except Exception:
        print('CAUGHT EXCEPTION')
        return errormsg()

@app.route('/api/capabilities/', methods=["POST"])
def api_capabilities():
    try:
        constituencies = request.get_json(force=True)
        election_system = ElectionSystem()
        capabilities_dict = {
            "election_system": election_system,
            "sim_settings": simulate.SimulationSettings(),
            "capabilities": {
                "use_thresholds": dictionaries.USE_THRESHOLDS,
                "systems": dictionaries.RULE_NAMES,
                "divider_rules": dictionaries.DIVIDER_RULE_NAMES,
                "cpu_counts": get_cpu_counts(),
                "adjustment_methods": dictionaries.ADJUSTMENT_METHOD_NAMES,
                "generating_methods": dictionaries.GENERATING_METHOD_NAMES,
                "seat_spec_options": dictionaries.SEAT_SPECIFICATION_OPTIONS,
                "scaling_names": dictionaries.SCALING_NAMES,
                "adj_threshold_choice": dictionaries.THRESHOLD_CHOICE,
            },
            "constituencies": constituencies
        }
        return jsonify(capabilities_dict)
    except Exception:
        return errormsg()

@app.route('/api/presets/', methods=["GET"])
def api_presets():
    try:
        presets_dict = get_presets_dict()
        return jsonify(presets_dict)
    except Exception:
        return errormsg()

@app.route('/api/simdownload/', methods=['GET','POST'])
def api_simdownload():
    try:
        simid = getparam('simid')
        tmpfilename = tempfile.mktemp(prefix=f'votesim-{simid[:6]}')
        simulation_to_excel(simid, tmpfilename)
        save_disparity_data(simid)
        date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
        download_name = f"simulation-{date}.xlsx"
        return save_file(tmpfilename, download_name);
    except Exception:
        return errormsg()

def get_presets_dict():
    with open('../data/presets.json', encoding='utf-8') as js:
        data = json.load(js)
    return data

if __name__ == '__main__':
    debug = os.environ.get("FLASK_DEBUG", "") == "True"
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = os.environ.get("FLASK_RUN_PORT", "5000")
    print(f"Running on {host}:{port}")
    app.debug = debug
    create_SIMULATIONS()
    if os.environ.get("HTTPS", "") == "True":
        print('Running server using HTTPS!')
        app.run(host=host, port=port, debug=debug, ssl_context="adhoc")
    else:
        print('Running server using HTTP (not secure)!')
        app.run(host=host, port=port, debug=debug)
