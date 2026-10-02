import os, tempfile, json
from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
from traceback import format_exc

import dictionaries, noweb, simulate
from excel_util import simulation_to_xlsx, votes_to_excel
from electionSystem import ElectionSystem
from electionHandler import ElectionHandler, update_constituencies
from input_util import check_simul_settings, check_system_names
from input_files import (
    load_section, validate_systems, validate_settings,
    prepare_simulation_inputs,
)
from util import get_cpu_counts
from trace_util import short_traceback
from noweb import load_votes, load_json, single_election
from noweb import new_simulation, check_simulation
from noweb import create_SIMULATIONS
from vote_table import check_vote_table

# Initialize process-local simulation state when imported by a WSGI server as
# well as when this module is run directly.
create_SIMULATIONS()

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
    return render_template("index.html")

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
        vote_table = check_vote_table(vote_table)
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
        payload = request.get_json(force=True)
        vote_table = payload['vote_table']
        systems = payload['systems']
        vote_table = check_vote_table(vote_table)
        handler = ElectionHandler(vote_table, systems, use_thresholds=True)
        tmpfilename = tempfile.mktemp(prefix='election-')
        handler.to_xlsx(tmpfilename, payload.get('display_settings'))
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
        vote_table = check_vote_table(vote_table)
        [constituencies, nat_seats] = update_constituencies(vote_table, systems)
        return jsonify({"constituencies": constituencies, "nat_seats":nat_seats})
    except Exception:
        return errormsg()

SYSTEM_DOWNLOAD_KEYS = [
    "name", "seat_spec_options", "constituencies",
    "constituency_threshold", "fixed_seat_national_threshold",
    "fixed_seat_threshold_choice",
    "adjustment_threshold", "adjustment_threshold_seats",
    "adj_threshold_choice", "require_votes_in_all_constituencies",
    "special_rules", "regional_adjustment_method",
    "adjustment_method", "primary_divider",
    "adj_determine_divider", "regional_adjustment_divider",
    "adj_alloc_divider", "nat_seats"
]

def downloadable_systems(systems):
    check_system_names(systems)
    return [{key: system[key] for key in SYSTEM_DOWNLOAD_KEYS}
            for system in systems]


def save_json(contents, prefix):
    tmpfilename = tempfile.mktemp(prefix=prefix + '-')
    with open(tmpfilename, 'w', encoding='utf-8') as jsonfile:
        json.dump(contents, jsonfile, ensure_ascii=False, indent=2)
    date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
    return save_file(tmpfilename, f"{prefix}-{date}.json")


@app.route('/api/systems/save/', methods=['POST'])
def api_systems_save():
    try:
        systems = downloadable_systems(getparam("systems"))
        return save_json({"systems": systems}, "electoral-systems")
    except Exception:
        return errormsg()


@app.route('/api/systems/upload/', methods=['POST'])
def api_systems_upload():
    try:
        systems = validate_systems(load_section(getfileparam(), "systems"))
        return jsonify({"systems": systems})
    except ValueError as error:
        return errormsg(str(error))
    except Exception:
        return errormsg()


@app.route('/api/simulation-settings/save/', methods=['POST'])
def api_simulation_settings_save():
    try:
        settings = getparam("sim_settings")
        check_simul_settings(settings.copy())
        return save_json({"sim_settings": settings}, "simulation-settings")
    except Exception:
        return errormsg()


@app.route('/api/simulation-settings/upload/', methods=['POST'])
def api_simulation_settings_upload():
    try:
        settings = load_section(getfileparam(), "sim_settings")
        settings = validate_settings(settings)
        return jsonify({"sim_settings": settings})
    except ValueError as error:
        return errormsg(str(error))
    except Exception:
        return errormsg()


@app.route('/api/settings/save/', methods=['POST'])
def api_settings_save():
    try:
        (systems, sim_settings) = getparam("systems", "sim_settings")
        names = []
        electoral_system_list = downloadable_systems(systems)
        for system in systems:
            names.append(system["name"])
        file_content = {
            "systems": electoral_system_list,
            "sim_settings": check_simul_settings(sim_settings)
        }
        filename = secure_filename(".".join(names))
        return save_json(file_content, filename)
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
        contents["vote_table"] = check_vote_table(contents["vote_table"])
        check_system_names(contents["systems"])
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
            return errormsg('Not a legal json-file for "Load all"')
    except Exception:
        return errormsg()

@app.route('/api/votes/save/', methods=['POST'])
def api_votes_save():
    try:
        vote_table = check_vote_table(getparam("vote_table"))
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
        name = "-".join(
            preset[key] for key in ("Country", "Name", "Year")
            if preset[key] not in ("", "-"))
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
        votes, systems, sim_settings = prepare_simulation_inputs(
            votes, systems, sim_settings)
        if sim_settings["simulation_count"] <= 0:
            raise ValueError("Number of simulations must be positive")
        simid = new_simulation(votes, systems, sim_settings)
        return jsonify({"started": True, "simid": simid})
    except ValueError as e:
        return errormsg(f"Error: {e}")
    except Exception:
        return errormsg()

@app.route('/api/simulate/check/', methods=['POST'])
def api_simulate_check():
    try:
        (simid,stop) = getparam("simid", "stop")
        (status, results) = check_simulation(simid, stop)
        if status['done'] and not results:
            raise RuntimeError('Results unavailable')
        return jsonify({"status": status, "results": results})
    except Exception:
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
                "flexible_adjustment_methods": sorted(
                    dictionaries.FLEXIBLE_ADJUSTMENT_METHODS),
                "special_rules": dictionaries.SPECIAL_RULE_NAMES,
                "regional_adjustment_methods":
                    dictionaries.REGIONAL_ADJUSTMENT_METHOD_NAMES,
                "election_law_presets": dictionaries.ELECTION_LAW_PRESETS,
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
        payload = request.get_json(force=True)
        simid = payload['simid']
        tmpfilename = tempfile.mktemp(prefix=f'votesim-{simid[:6]}')
        simulation = noweb.SIMULATIONS[simid]
        result = simulation['result'].get_result_web(
            simulation['kind'] == 'parallel')
        simulation_to_xlsx(result, tmpfilename, payload.get('display_settings'))
        date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
        download_name = f"simulation-{date}.xlsx"
        return save_file(tmpfilename, download_name);
    except Exception:
        return errormsg()

def get_presets_dict():
    with open('../data/presets.json', encoding='utf-8') as js:
        data = json.load(js)
    return data

def default_port():
    if "FLASK_RUN_PORT" in os.environ:
        return os.environ["FLASK_RUN_PORT"]
    hostname = os.uname().nodename.lower()
    return "5000" if hostname.startswith("pluto") else "5001"

if __name__ == '__main__':
    debug = os.environ.get("FLASK_DEBUG", "") == "True"
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = default_port()
    print(f"Running on {host}:{port}")
    app.debug = debug
    if os.environ.get("HTTPS", "") == "True":
        print('Running server using HTTPS!')
        app.run(host=host, port=port, debug=debug, ssl_context="adhoc")
    else:
        print('Running server using HTTP (not secure)!')
        app.run(host=host, port=port, debug=debug)
