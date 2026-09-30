# Voting system simulator

The Voting system simulator is a web application and Python calculation engine
for studying proportional electoral systems. It allocates constituency and
adjustment seats, calculates a single election under one or more electoral
systems, and compares systems over simulated elections.

The simulator is intended for statutory, comparative, and hypothetical work.
It includes allocation methods used in Iceland, Norway, Sweden, Finland and
Denmark, biproportional methods such as alternating scaling, configurable
thresholds and divisor rules, and Excel export of election and simulation results.

The browser interface is built with Vue and the HTTP API with Flask. The
allocation and simulation code is under `backend/` and can also be run without
the browser.

## Offline simulations

Use a vote-table CSV in the standard vote format (for example, one under `data/`).
Download the systems from **Electoral systems** and the settings from
**Simulated elections**.
After `uv sync --locked`, activate the virtual environment and run from the
repository root:

```sh
source .venv/bin/activate
./backend/sim.py \
  -v votes.csv -e electoral-systems.json \
  -s simulation-settings.json -o results.csv \
  -r 1000 -C 4 -S 12345
```

Alternatively, use the simulator's **Download all** JSON file:

```sh
./backend/sim.py -a simulator.json -o results.csv -r 1000 -C 4 -S 12345
```

The three overrides are optional; otherwise their values come from the settings
file. `--seed -` requests fresh random draws. The offline runner always enables
sensitivity at perturbation CoVs of 0.3%, 1%, and 3%; its number of perturbations
per simulation and generating distribution come from the settings file.

The UTF-8 CSV has one column per electoral system. Each quality-measure and
sensitivity row has separate entries for the mean, standard deviation, and
lower and upper 95% confidence limits. Entropy scores are percentages; their
cells are blank when the chosen rule does not support that score.

Use `-O statistics.json` to save mergeable simulation statistics. You can use
`-O` alone or together with `-o results.csv`. The JSON can be read with
`simulation_chunks.read_chunk_result` and combined with other replicate ranges
using `simulation_chunks.combine_chunks`. For a separate range, pass its
zero-based first replicate number with `-i` (for example, `-i 1000`). Runs
intended for merging should use the same seed and disjoint replicate ranges.

## Run locally

Requirements:

- Git
- [uv](https://docs.astral.sh/uv/)
- Python 3.10 or later (selected by `uv`)
- Node.js and npm; use a maintained LTS release

Clone the repository and install the locked dependencies:

```sh
git clone https://github.com/jonasson2/voting.git
cd voting
uv sync --locked
cd vue-frontend
npm ci
npm run build
cd ../backend
uv run --locked python web.py
```

By default, open <http://localhost:5001>. Set `FLASK_RUN_PORT` to use a
different local port:

```sh
FLASK_RUN_PORT=5050 uv run --locked python web.py
```

Confirm that the service is available with:

```sh
curl -I http://localhost:5001
```

Stop the local server with `Ctrl-C` in the terminal where `web.py` is running.
If port 5001 is already in use, either stop the process using it or choose a
different port with `FLASK_RUN_PORT` as shown above.

After the first installation, rebuild the frontend only when its source has
changed. `npm ci` may report dependency deprecation or audit warnings; these do
not prevent the documented frontend build from completing. Review and update
dependencies separately before deploying a public service.

## Quick persistent testing with GNU Screen

GNU Screen is a convenient intermediate option when a test server needs to
survive a disconnected SSH session, but does not need production supervision.
Start a named session from the repository:

```sh
screen -S voting
cd backend
FLASK_RUN_HOST=127.0.0.1 uv run --locked python web.py
```

Detach without stopping Flask by pressing `Ctrl-A`, then `D`. The shell can then
be closed. List or reconnect to the session later with:

```sh
screen -ls
screen -r voting
```

To stop the server cleanly, reconnect, press `Ctrl-C`, and run `exit`. To discard
the entire session from outside it, use:

```sh
screen -S voting -X quit
```

The included `runvoting.sh` script automates branch updates, frontend builds,
and named Screen-session restarts. Use it only from a clean checkout because it
checks out and pulls the requested branch:

```sh
FLASK_RUN_HOST=127.0.0.1 ./runvoting.sh main
```

Binding to `127.0.0.1` prevents direct network access. Use an SSH tunnel to
reach a remote test server. Screen does not restart the application after a
crash or reboot, and this method still uses Flask's development server; use the
systemd procedure in [the deployment guide](doc/deployment.md) for a durable
HTTPS deployment.

## Deploy publicly

The complete systemd, HTTPS reverse-proxy, operations, and troubleshooting
guide is in [doc/deployment.md](doc/deployment.md).

## Tests

Run the backend regression suite through the locked environment:

```sh
cd backend
uv run --locked python test.py
```

Verify the frontend build with:

```sh
cd vue-frontend
npm ci
npm run build
npm run build-production
```

## Repository layout

- `backend/`: allocation methods, simulations, Flask API, and tests
- `vue-frontend/`: Vue application and static assets
- `data/`: example election data, presets, and data-source scripts
- `deploy/`: systemd and reverse-proxy production-service examples
- `doc/`: technical and user documentation

## License and authors

Released under the [GNU Affero General Public License version 3](LICENSE).

Authors and contributors:
Smári McCarthy
Þorkell Helgason
Martha Guðrún Bjarnadóttir
Pétur Ólafur Aðalgeirsson
Helgi Hrafn Gunnarsson
Bjartur Thorlacius
Lilja Steinunn Jónsdóttir
Kristján Jónasson

Current maintainer: **Kristján Jónasson**.
