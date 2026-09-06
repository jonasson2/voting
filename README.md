# Voting system simulator

The Voting system simulator is a web application and Python calculation engine
for studying proportional electoral systems. It allocates constituency and
adjustment seats, calculates a single election under one or more electoral
systems, and compares systems over simulated elections.

The simulator is intended for statutory, comparative, and hypothetical work.
It includes allocation methods used in Iceland and Norway, biproportional
methods such as alternating scaling, configurable thresholds and divisor rules,
and Excel export of election and simulation results.

The browser interface is built with Vue and the HTTP API with Flask. The
allocation and simulation code is under `backend/` and can also be run without
the browser.

## Run locally

Requirements:

- Git
- [uv](https://docs.astral.sh/uv/)
- Python 3.9 or later (selected by `uv`)
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

By default, open <http://localhost:8080>. Set `FLASK_RUN_PORT` to use a
different local port:

```sh
FLASK_RUN_PORT=5000 uv run --locked python web.py
```

Confirm that the service is available with:

```sh
curl -I http://localhost:8080
```

Stop the local server with `Ctrl-C` in the terminal where `web.py` is running.
If port 8080 is already in use, either stop the process using it or choose a
different port with `FLASK_RUN_PORT` as shown above.

After the first installation, rebuild the frontend only when its source has
changed. `npm ci` may report dependency deprecation or audit warnings; these do
not prevent the documented frontend build from completing. Review and update
dependencies separately before deploying a public service.

## Run without the browser

`single.py` runs one election directly from the command line. Run it from
`backend/`; give paths outside `backend/data/` explicitly:

```sh
cd backend
uv run --locked python single.py switch -v ../data/iceland-2021.csv
uv run --locked python single.py --help
```

The command writes `single.xlsx` and `votes.xlsx` in `backend/`.

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
FLASK_RUN_HOST=127.0.0.1 ./runvoting.sh dev
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
