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
- Node.js and npm

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

On the `dev` branch, open <http://localhost:8080>. Set `FLASK_RUN_PORT` to
override the branch default:

```sh
FLASK_RUN_PORT=5000 uv run --locked python web.py
```

After the first installation, rebuild the frontend only when its source has
changed.

## Run without the browser

`single.py` runs one election directly from the command line. Run it from
`backend/`; give paths outside `backend/data/` explicitly:

```sh
cd backend
uv run --locked python single.py switch -v ../data/iceland-2021.csv
uv run --locked python single.py --help
```

The command writes `single.xlsx` and `votes.xlsx` in `backend/`.

## Run on a server

The repository includes `runvoting.sh` for a persistent deployment using GNU
Screen. A server needs Git, uv, Node.js, npm, and Screen. For example, on Pluto:

```sh
ssh pluto
cd ~/voting
./runvoting.sh dev
```

The script updates and checks out the requested branch, installs frontend
packages when its lockfile has changed, builds the frontend, and starts Flask in
a detached Screen session. Running the same command again restarts that branch.

```sh
screen -ls
screen -r dev
```

Detach from Screen with `Ctrl-A`, then `D`.

The configured branch ports are:

| Branch | Local | Pluto |
| --- | ---: | ---: |
| `main` | 5001 | 5000 |
| `dev` | 8080 | 8080 |

The included launcher uses Flask's built-in server. A public deployment should
place it behind the server's usual firewall or reverse proxy.

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
```

## Repository layout

- `backend/`: allocation methods, simulations, Flask API, and tests
- `vue-frontend/`: Vue application and static assets
- `data/`: example election data, presets, and data-source scripts
- `doc/`: technical and user documentation

## License and authors

Released under the GNU Affero General Public License version 3.

The authors and contributors are Smári McCarthy, Þorkell Helgason, Martha Guðrún
Bjarnadóttir, Pétur Ólafur Aðalgeirsson, Helgi Hrafn Gunnarsson, Bjartur
Thorlacius, Lilja Steinunn Jónsdóttir, and Kristján Jónasson.

Current maintainer: **Kristján Jónasson**.
