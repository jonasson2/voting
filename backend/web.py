from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
import random
import os
import os.path
import tempfile
from datetime import datetime, timedelta
from hashlib import sha256
import json
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import csv

import dictionaries
from electionRules import ElectionRules
from electionHandler import ElectionHandler
import util
from excel_util import save_votes_to_xlsx
from input_util import check_input, check_vote_table, check_rules, check_simulation_rules
import voting
import simulate as sim

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
def get_new_download_id():
    global DOWNLOADS_IDX
    did = DOWNLOADS_IDX = DOWNLOADS_IDX + 1

    h = sha256()
    didbytes = (str(did) + ":" + str(random.randint(1, 100000000))).encode('utf-8')
    h.update(didbytes)
    return h.hexdigest()

@app.route('/api/downloads/get/', methods=['GET'])
def get_download():
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
        as_attachment=True
    )
    return response

def handle_election():
    data = request.get_json(force=True)
    data = check_input(data, ["vote_table", "rules"])

    handler = ElectionHandler(data["vote_table"], data["rules"])
    return handler

@app.route('/api/election/', methods=["POST"])
def get_election_results():
    try:
        result = handle_election().elections
    except (KeyError, TypeError, ValueError) as e:
        message = e.args[0]
        print("Error-1:",message)
        return jsonify({"error": message})
    result=[election.get_results_dict() for election in result]
    return jsonify(result)

@app.route('/api/election/save/', methods=['POST'])
def get_election_excel():
    handler = handle_election()
    tmpfilename = tempfile.mktemp(prefix='election-')
    handler.to_xlsx(tmpfilename)
    date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
    download_name=f"Election-{date}.xlsx"
    return save_file(tmpfilename, download_name)

@app.route('/api/settings/save/', methods=['POST'])
def save_settings():
    data = request.get_json(force=True)
    check_input(data, ["e_settings", "sim_settings"])

    settings = data["e_settings"]
    if type(settings) != list: settings = [settings]
    settings = check_rules(settings)

    #no need to expose more than the following keys
    keys = [
        "name", "seat_spec_option", "constituencies",
        "constituency_threshold", #"constituency_allocation_rule",
        "adjustment_threshold", #"adjustment_division_rule",
        "adjustment_method", #"adjustment_allocation_rule"
    ]

    names = []
    electoral_system_list = []
    for setting in settings:
        names.append(setting["name"])
        #electoral_system_list.append({key: setting[key] for key in keys})
        item = {key: setting[key] for key in keys}
        item["constituency_allocation_rule"] = setting["primary_divider"]
        item["adjustment_division_rule"]     = setting["adj_determine_divider"]
        item["adjustment_allocation_rule"]   = setting["adj_alloc_divider"]
        electoral_system_list.append(item)

    file_content = {
        "e_settings": electoral_system_list,
        "sim_settings": check_simulation_rules(data["sim_settings"]),
    }

    tmpfilename = tempfile.mktemp(prefix='e_settings-')
    with open(tmpfilename, 'w', encoding='utf-8') as jsonfile:
        json.dump(file_content, jsonfile, ensure_ascii=False, indent=2)
    filename = secure_filename(".".join(names))
    date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
    download_filename=f"{filename}-{date}.json"
    return save_file(tmpfilename, download_filename)

@app.route('/api/settings/upload/', methods=['POST'])
def upload_settings():
    if 'file' not in request.files:
        return jsonify({'error': 'must upload a file.'})
    f = request.files['file']
    file_content = json.load(f.stream)
    if type(file_content) == dict and "e_settings" in file_content:
        electoral_system_list = file_content["e_settings"]
        assert "sim_settings" in file_content
        sim_settings = check_simulation_rules(file_content["sim_settings"])
    else:
        electoral_system_list = file_content
        sim_settings = None
    assert type(electoral_system_list) == list

    keys = ["name", "seat_spec_option", "constituencies",
            "constituency_threshold", "constituency_allocation_rule",
            "adjustment_threshold", "adjustment_division_rule",
            "adjustment_method", "adjustment_allocation_rule"]
    settings = []
    for item in electoral_system_list:
        for info in keys:
            if info not in item:
                raise KeyError(f"{info} is missing from a setting in file.")
        if item["seat_spec_option"] == "defer":
            item["seat_spec_option"] = "refer"
        setting = ElectionRules()
        setting.update(item)
        setting["primary_divider"] = item["constituency_allocation_rule"]
        setting["adj_determine_divider"] = item["adjustment_division_rule"]
        setting["adj_alloc_divider"] = item["adjustment_allocation_rule"]
        settings.append(setting)

    settings = check_rules(settings)
    return jsonify({"e_settings": settings, "sim_settings": sim_settings})

@app.route('/api/votes/save/', methods=['POST'])
def save_votes():
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

@app.route('/api/votes/upload/', methods=['POST'])
def upload_votes():
    if 'file' not in request.files:
        return jsonify({'error': 'must upload a file.'})
    f = request.files['file']
    res = util.load_votes_from_stream(f.stream, f.filename)
    return jsonify(res)

@app.route('/api/votes/paste/', methods=['POST'])
def paste_votes():
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


SIMULATIONS = {}
SIMULATION_IDX = 0

def run_simulation(sid):
    global SIMULATIONS
    SIMULATIONS[sid][1].done = False
    print("Starting thread %s" % sid)
    SIMULATIONS[sid][0].simulate()
    print("Ending thread %s" % sid)
    SIMULATIONS[sid][1].done = True


def cleanup_expired_simulations():
    global SIMULATIONS
    global SIMULATION_IDX
    try:
        for sid, sim in list(SIMULATIONS.items()):
            if sim[2] < datetime.now():
                del(SIMULATIONS[sid])
    except RuntimeError:
        pass

@app.route('/api/simulate/', methods=['POST'])
def start_simulation():
    global SIMULATIONS
    global SIMULATION_IDX

    SIMULATION_IDX += 1

    h = sha256()
    sidbytes = (str(SIMULATION_IDX) + ":" + str(random.randint(1, 100000000))).encode('utf-8')
    h.update(sidbytes)
    sid = h.hexdigest()
    thread = threading.Thread(target=run_simulation, args=(sid,))

    try:
        simulation = set_up_simulation()
    except (KeyError, TypeError, ValueError) as e:
        message = e.args[0]
        print("Error-4", message)
        return jsonify({"started": False, "error": message})

    # Simulation cache expires in 3 hours = 3*3600 = 10800 seconds
    expires = datetime.now() + timedelta(seconds=10800)
    SIMULATIONS[sid] = [simulation, thread, expires]

    # Whenever we start a new simulation, we'll clean up any expired
    #   simulations first:
    cleanup_expired_simulations()

    thread.start()
    return jsonify({"started": True, "sid": sid})


@app.route('/api/simulate/check/', methods=['GET', 'POST'])
def check_simulation():
    global SIMULATIONS
    data = request.get_json(force=True)
    msg = ""
    if "sid" not in data:
        msg = "Please supply a SID."
    elif data["sid"] not in SIMULATIONS:
        msg = "Please supply a valid SID."
    else:
        # print(f"{SIMULATIONS=}")
        # print(f'{data["sid"] in SIMULATIONS=}')
        # print(f'{SIMULATIONS[data["sid"]]=}')
        simulation, thread, expiry = SIMULATIONS[data["sid"]]
        #if thread.done:
        #    del(SIMULATIONS[data["sid"]])
        if not hasattr(simulation,"iteration_time"):
            print("no iteration_time in result")
            simulation.iteration_time = 0
        try:
            #print("simulation contents:")
            #print(simulation.__dict__.keys())
            simulation.iteration -= simulation.iterations_with_no_solution
            return_dict = {
                "done": thread.done,
                "iteration": simulation.iteration,
                "time_left": simulation.time_left,
                "iteration_time": simulation.iteration,
                "target": simulation.sim_rules["simulation_count"],
                "results": simulation.get_results_dict(),
                "parties": simulation.parties,
                "e_rules": simulation.e_rules
            }
        except Exception as e:           
            msg = "Error in check_simulation: " + str(e)
    if len(msg) > 0:
        print("Error; message = ", msg)
        return jsonify({"error": msg})
    else:
        return jsonify(return_dict)

@app.route('/api/simulate/stop/', methods=['GET', 'POST'])
def stop_simulation():
    data = request.get_json(force=True)
    if "sid" not in data:
        return jsonify({"error": "No simulation id supplied to backend."})
    if data["sid"] not in SIMULATIONS:
        return jsonify({"error": "Unknown simulation id supplied to backend."})
    simulation, thread, expiry = SIMULATIONS[data["sid"]]

    simulation.terminate = True
    thread_done = thread.done # Get done status (thread.join() finishes the thread and
                              # sets thread.done to True
    thread.join()
    #if thread.done:
    #    del(SIMULATIONS[data["sid"]])

    return jsonify({
        "done": thread_done,
        "iteration": simulation.iteration,
        "target": simulation.sim_rules["simulation_count"],
        "results": simulation.get_results_dict()
    })

def set_up_simulation():
    # TODO make following settable in vue
    data = request.get_json(force=True)
    data = check_input(data,
        ["vote_table", "election_rules", "simulation_rules"])
    vote_table = data["vote_table"]
    rulesets = []
    for rs in data["election_rules"]:
        election_rules = ElectionRules()
        election_rules.update(rs)
        rulesets.append(election_rules)
    simulation_rules = sim.SimulationRules()
    simulation_rules.update(check_simulation_rules(data["simulation_rules"]))
    simulation = sim.Simulation(simulation_rules, rulesets, vote_table)
    return simulation


@app.route('/api/script/', methods=["POST"])
def handle_api():
    script = request.get_json(force=True)
    if not script or script == {}:
        return jsonify({"error": "No script sent"})
    e = run_script(script)
    if type(e) == dict:
        return jsonify(e)
    return jsonify(e.get_results_dict())

@app.route('/api/capabilities/', methods=["GET"])
def handle_capabilities():
    capabilities_dict = get_capabilities_dict()
    return jsonify(capabilities_dict)

@app.route('/api/presets/', methods=["GET"])
def get_presets_list():
    presets_dict = get_presets_dict()
    return jsonify(presets_dict)

@app.route('/api/presets/load/', methods=['POST'])
def get_preset():
    qv = request.get_json(force=True)
    if 'eid' not in qv:
        return jsonify({'error': 'Must supply eid'})
    prs = get_presets_dict()
    # TODO: This is silly but it paves the way to a real database
    for p in prs:
        if p['id'] == qv['eid']:
            res = util.load_votes_from_stream(open('../data/elections/%s' % p['filename'], "r"), p['filename'])
            return jsonify(res)

@app.route('/api/simdownload/', methods=['GET','POST'])
def save_simulation():
    data = request.get_json(force=True)
    sid = data["sid"]
    tmpfilename = tempfile.mktemp(prefix=f'votesim-{sid[:6]}')
    (simulation, thread, expiry) = SIMULATIONS[sid]
    simulation.to_xlsx(tmpfilename)
    date = datetime.now().strftime('%Y.%m.%dT%H.%M.%S')
    download_name = f"simulation-{date}.xlsx"
    return save_file(tmpfilename, download_name);

def get_capabilities_dict():
    return {
        "election_rules": ElectionRules(),
        "simulation_rules": sim.SimulationRules(),
        "capabilities": {
            "rules": dictionaries.RULE_NAMES,
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
        data = {'error': 'Could not load presets: database lost.'}
    #except json.decoder.JSONDecodeError:
    #    data = {'error': 'Could not load presets due to parse error.'}

    return data

def run_script(rules):
    if type(rules) in ["str", "unicode"]:
        with open(rules, "r") as read_file:
            rules = json.load(read_file)

    if type(rules) != dict:
        return {"error": "Incorrect script format."}

    if rules["action"] not in ["simulation", "election"]:
        return {"error": "Script action must be election or simulation."}

    if rules["action"] == "election":
        return voting.run_script_election(rules)

    else:
        return sim.run_script_simulation(rules)

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
