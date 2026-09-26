## Model scope

The Voting simulator supports statutory, comparative, and hypothetical applications
of allocation algorithms.

Do not enforce a country's complete legal seat structure merely because a method is
named after that country. For example, `norwegian-law` may be used with zero, one,
or several adjustment seats per constituency. 

## Changes

- To restart the local simulator on port 5001, run `./restart-local.sh` from
  the repository root. It stops the current listener, rebuilds the frontend,
  and starts the backend in the background; logs go to `tmp/web-5001.log`.
- Add or update focused regression tests for allocation and input-handling bugs.
- Scale verification to the risk of the change. For copy, labels, or narrowly
  scoped CSS adjustments, inspect the diff and run only a directly relevant
  syntax or focused check when one exists; do not automatically run full test
  suites or a production build.
- Run focused tests after behavioral changes. Run `python test.py` from
  `backend/`, the frontend suite, and the frontend build before a substantial
  checkpoint, or when shared/core behavior has changed.
- Keep parsers and generated election data under `data/` and record sources in
  `data/sources.txt`.

## Responses

- Never append generated follow-up links or action links. They are not rendered
  as functional links in the command-line interface used for this project and
  are therefore useless to the user.
- Prefer plain-text "pidgin math" to LaTeX notation in answers. Use formal
  typeset formulas only when plain-text notation would make the explanation
  materially less clear.
