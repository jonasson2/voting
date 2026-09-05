# Session context

Project: `/Users/jonasson/drive/voting`  
Branch: `dev`

Read `AGENTS.md` first. The simulator is a Vue 2 frontend and Flask/Python backend.
README files may be outdated; inspect source instead.

The local app is currently running at <http://127.0.0.1:8080/>.

## Structure

- `backend/web.py`: Flask API and frontend serving.
- `backend/voting.py`: central single-election allocation flow.
- `backend/apportion.py`: one-dimensional apportionment and thresholds.
- `backend/methods/`: adjustment-seat methods.
- `vue-frontend/src/`: Vue UI.
- `data/`: vote CSVs, parsers, presets, and sources.

## Recent uncommitted work

- Norwegian 2017, 2021, and 2025 data and parser improvements.
- Swedish 2014, 2018, and 2022 data, parser, and per-election party abbreviations.
- `data/sources.txt` with official sources and Wikipedia cross-check notes.
- Removal of `data/parse-hagstofa.py`.
- Backend fixes:
  - corrected the `average` national-vote basis;
  - corrected browser CSV upload;
  - made percentage thresholds inclusive;
  - relabelled “Swedish switching” as “Swedish-style switching”;
  - added `backend/tests/test_current.py`;
  - made `python test.py` run current tests and exit nonzero on failure.

Verify backend changes with:

```sh
cd /Users/jonasson/drive/voting/backend
python test.py
```

Four current tests pass.

## Modelling policy

Do not add validations that force statutory country structures. Methods are intentionally
usable out of country; for example, the Norwegian allocation method may be applied
with zero, one, or multiple adjustment seats per constituency. Describe this as a
comparative or hypothetical model, not necessarily a full statutory reproduction.

## Data status

- Norway data is registered in `data/presets.json`.
- Swedish data is in `data/sweden_2014.csv`, `data/sweden_2018.csv`, and
  `data/sweden_2022.csv`, but is not yet registered as frontend presets.
- Swedish files expand small parties rather than retaining an aggregate OVR party, so
  an aggregate residual cannot receive seats.

## Related article project

- `/Users/jonasson/drive/kosningagrein`
- Working title: “Simulating Constituency-Based Proportional Seat Allocation”.
- `article-frame.md` is its working English outline.
