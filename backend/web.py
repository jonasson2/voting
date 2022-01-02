from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import tempfile
from datetime import datetime, timedelta
import json
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import csv

import dictionaries
from electionSystem import ElectionSystem
from electionHandler import ElectionHandler, update_constituencies
import util
from excel_util import save_votes_to_xlsx
from input_util import check_input, check_vote_table, check_systems
from input_util import check_simul_settings
import voting
import simulate
from util import disp, short_traceback
from noweb import load_votes, load_systems, single_election, load_all
from noweb import start_simulation, check_simulation, SIMULATIONS
from noweb import simulation_to_excel
from traceback import format_exc

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

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static/', path)

DOWNLOADS = {}
DOWNLOADS_IDX = 0

@app.route('/api/downloads/get/', methods=['GET'])
def api_downloads_get():
    global DOWNLOADS
    if "id" not in request.args:
        return jsonify({'error': 'Please supply a download id.'})
    if request.args["id"] not in DOWNLOADS:
        return jsonify({"error": "Please supply a valid download id."})
    tmpfilename, attachment_filename = DOWNLOADS[request.args["id"]]

    content = send_from_directory(
        directory=os.path.dirname(tmpfilename),
        path=os.path.basename(tmpfilename),
        attachment_filename=attachment_filename,
        as_attachment=False
    )

    return content

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

@app.route('/api/election/', methods=["POST"])
def api_election():
    try:
        data = request.get_json(force=True)
        data = check_input(data, ["vote_table", "systems"])
        data = check_input(data, ["vote_table", "systems"])
        vote_table = data["vote_table"]
        systems = data["systems"]
        if len(systems) == 0 or len(systems[0]) == 0:
            raise Exception("/api/election posted with no electoral system")
        constituencies = update_constituencies(vote_table, systems)
        for (c,s) in zip(constituencies, systems):
            s["constituencies"] = c
        results = single_election(vote_table, systems);
        return jsonify({"results": results, "systems": systems})
    except Exception:
        message = format_exc()
        print("ERROR: ", message)
        return jsonify({"error": message})

@app.route('/api/election/save/', methods=['POST'])
def api_election_save():
    try:
        data = request.get_json(force=True)
        data = check_input(data, ["vote_table", "systems"])
        systems = data["systems"]
        vote_table = data["vote_table"]
        handler = ElectionHandler(vote_table, systems)
        tmpfilename = tempfile.mktemp(prefix='election-')
        handler.to_xlsx(tmpfilename)
        date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
        download_name=f"Election-{date}.xlsx"
    except Exception:
        message = format_exc()
        return jsonify({"error": message})
    return save_file(tmpfilename, download_name)

@app.route('/api/settings/update_constituencies/', methods=["POST"])
def api_update_constituencies():
    # Update constituencies in electoral systems according to
    # the current vote table and systems[:]["seat_spec_option"]
    data = request.get_json(force=True)
    vote_table = data["vote_table"]
    systems = data["systems"]
    try:
        constituencies = update_constituencies(vote_table, systems)
        return jsonify({"constituencies": constituencies})
    except Exception:
        message = format_exc()
        print("ERROR: ", message)
        return jsonify({"error": message})

@app.route('/api/settings/save/', methods=['POST'])
def api_settings_save():
    data = request.get_json(force=True)
    try:
        check_input(data, ["systems", "sim_settings"])
    except Exception:
        print("caught exception")
        message = format_exc()
        return jsonify({"error": message})
    systems = data["systems"]
    systems = check_systems(systems)
    
    #no need to expose more than the following keys
    keys = [
        "name", "seat_spec_option", "constituencies",
        "compare_with",
        "constituency_threshold", #"constituency_allocation_rule",
        "adjustment_threshold", #"adjustment_division_rule",
        "adjustment_method", #"adjustment_allocation_rule"
    ]

    names = []
    electoral_system_list = []
    for system in systems:
        names.append(system["name"])
        #electoral_system_list.append({key: system[key] for key in keys})
        item = {key: system[key] for key in keys}
        item["constituency_allocation_rule"] = system["primary_divider"]
        item["adjustment_division_rule"]     = system["adj_determine_divider"]
        item["adjustment_allocation_rule"]   = system["adj_alloc_divider"]
        electoral_system_list.append(item)

    file_content = {
        "e_settings": electoral_system_list,
        "sim_settings": check_simul_settings(data["sim_settings"]),
    }
    tmpfilename = tempfile.mktemp(prefix='e_settings-')
    with open(tmpfilename, 'w', encoding='utf-8') as jsonfile:
        json.dump(file_content, jsonfile, ensure_ascii=False, indent=2)
    filename = secure_filename(".".join(names))
    date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
    download_filename=f"{filename}-{date}.json"
    return save_file(tmpfilename, download_filename)

@app.route('/api/settings/upload/', methods=['POST'])
def api_settings_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'must upload a file.'})
    f = request.files['file']
    systems, sim_settings = load_systems(f)
    return jsonify({"systems": systems, "sim_settings": sim_settings})

@app.route('/api/votes/save/', methods=['POST'])
def api_votes_save():
    data = request.get_json(force=True)    
    vote_table = check_vote_table(data["vote_table"])
    file_matrix = [
        [vote_table["name"], "cons", "adj"] + vote_table["parties"],
    ] + [
        [
            vote_table["constituencies"][c]["name"],
            vote_table["constituencies"][c]["num_const_seats"],
            vote_table["constituencies"][c]["num_adj_seats"],
        ] + vote_table["votes"][c]
        for c in range(len(vote_table["constituencies"]))
    ]    
    tmpfilename = tempfile.mktemp(prefix='vote_table-')
    save_votes_to_xlsx(file_matrix, tmpfilename)
    download_name = secure_filename(vote_table['name']) + ".xlsx"
    return save_file(tmpfilename, download_name);

@app.route('/api/votes/saveall/', methods=['POST'])
def api_votes_save_all():
    data = request.get_json(force=True)
    contents = {
        "vote_table": data["vote_table"],
        "systems": data["systems"],
        "sim_settings": data["sim_settings"]
    }
    tmpfilename = tempfile.mktemp(prefix='simulator-')
    with open(tmpfilename, 'w', encoding='utf-8') as jsonfile:
        json.dump(contents, jsonfile, ensure_ascii=False, indent=2)
    date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
    download_filename = "simulator-" + date + ".json"
    return save_file(tmpfilename, download_filename)

@app.route('/api/votes/uploadall/', methods=['POST'])
def api_votes_uploadall():
    f = request.files['file']
    content = load_all(f)
    return jsonify(content)

@app.route('/api/votes/upload/', methods=['POST'])
def api_votes_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'must upload a file.'})
    f = request.files['file']
    res = util.load_votes_from_stream(f.stream, f.filename)
    return jsonify(res)

@app.route('/api/votes/paste/', methods=['POST'])
def api_votes_paste():
    data = request.get_json(force=True)

    if "csv" not in data:
        return jsonify({'error': 'must provide csv'})

    rd = []
    for row in csv.reader(StringIO(data["csv"]), skipinitialspace=True):
        rd.append(row)

    return jsonify(util.parse_input(
        input=rd,
        name_included=data["has_name"],
        parties_included=data["has_parties"],
        const_included=data["has_constituencies"],
        const_seats_included=data["has_constituency_seats"],
        adj_seats_included=data["has_constituency_adjustment_seats"]
    ))

@app.route('/api/simulate/', methods=['POST'])
def api_simulate():
    try:
        data = request.get_json(force=True)
        data = check_input(data, ["vote_table", "systems", "sim_settings"])
        votes = data["vote_table"]
        systems = data["systems"]
        sim_settings = data["sim_settings"]
        sid = start_simulation(votes, systems, sim_settings)
        return jsonify({"started": True, "sid": sid})
    except Exception:
        message = short_traceback(format_exc())
        print("Length of message = ", len(message))
        print("Error; message = ", message)
        return jsonify({"started": False, "error": message})

@app.route('/api/simulate/check/', methods=['POST'])
def api_simulate_check():
    data = request.get_json(force=True)
    try:
        sid = data["sid"]
        stop = data["stop"]
        (status, results) = check_simulation(sid, stop)
    except Exception:
        msg = short_traceback(format_exc())
        return jsonify({"error": msg})
    return jsonify({"status": status, "results": results})

@app.route('/api/capabilities/', methods=["POST"])
def api_capabilities():
    constituencies = request.get_json(force=True)
    capabilities_dict = get_capabilities_dict()
    capabilities_dict["constituencies"] = constituencies
    #disp("capabilities_dict", capabilities_dict)
    return jsonify(capabilities_dict)

@app.route('/api/presets/', methods=["GET"])
def api_presets():
    presets_dict = get_presets_dict()
    return jsonify(presets_dict)

@app.route('/api/presets/load/', methods=['POST'])
def api_presets_load():
    qv = request.get_json(force=True)
    if 'eid' not in qv:
        return jsonify({'error': 'Must supply eid'})
    prs = get_presets_dict()
    # TODO: This is silly but it paves the way to a real database
    for p in prs:
        if p['id'] == qv['eid']:
            print('p=', p)
            print(type(p['filename']))
            res = load_votes(p['filename'], preset=True)
            return jsonify(res)

@app.route('/api/simdownload/', methods=['GET','POST'])
def api_simdownload():
    try:
        data = request.get_json(force=True)
        sid = data["sid"]
        tmpfilename = tempfile.mktemp(prefix=f'votesim-{sid[:6]}')
        print("tmpfilename", tmpfilename)
        simulation_to_excel(sid, tmpfilename)
    except Exception:
        message = format_exc()
        return jsonify({"error": message})
    date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
    download_name = f"simulation-{date}.xlsx"
    print("download_name", download_name)
    return save_file(tmpfilename, download_name);

def get_capabilities_dict():
    election_system = ElectionSystem()
    return {
        "election_system": election_system,
        "sim_settings": simulate.SimulationSettings(),
        "capabilities": {
            "systems": dictionaries.RULE_NAMES,
            "divider_rules": dictionaries.DIVIDER_RULE_NAMES,
            "adjustment_methods": dictionaries.ADJUSTMENT_METHOD_NAMES,
            "generating_methods": dictionaries.GENERATING_METHOD_NAMES,
            "seat_spec_options": dictionaries.SEAT_SPECIFICATION_OPTIONS,
        },
    }

def get_presets_dict():
    try:
        with open('../data/presets.json', encoding='utf-8') as js:
            data = json.load(js)
    except IOError:
        data = {'error': 'Could not load presets: database lost?'}
    except Exception:
        data = {'error': format_exc()}
        
    #except json.decoder.JSONDecodeError:
    #    data = {'error': 'Could not load presets due to parse error.'}

    return data

def run_script(systems):
    if type(systems) in ["str", "unicode"]:
        with open(systems, "r") as read_file:
            systems = json.load(read_file)

    if type(systems) != dict:
        return {"error": "Incorrect script format."}

    if systems["action"] not in ["simulation", "election"]:
        return {"error": "Script action must be election or simulation."}

    if systems["action"] == "election":
        return voting.run_script_election(systems)

    else:
        return simulate.run_script_simulation(systems)

if __name__ == '__main__':
    debug = os.environ.get("FLASK_DEBUG", "") == "True"
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = os.environ.get("FLASK_RUN_PORT", "5000")
    print(f"Running on {host}:{port}")
    app.debug = debug
    if os.environ.get("HTTPS", "") == "True":
        print('Running server using HTTPS!')
        app.run(host=host, port=port, debug=debug, ssl_context="adhoc")
    else:
        print('Running server using HTTP (not secure)!')
        app.run(host=host, port=port, debug=debug)
