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
- Run focused tests after behavioural changes. Run `python test.py` from
  `backend/`, the frontend suite, and the frontend build before a substantial
  checkpoint, or when shared/core behaviour has changed.
- Keep parsers and generated election data under `data/` and record sources in
  `data/sources.txt`.

## Elja workflow

- Develop and edit code in the local repository. Commit and push those changes
  from the local repository, then pull them into `~/voting` on Elja before
  running there.
- Do not edit or replace tracked code directly on Elja. Keep Elja-only inputs
  and simulation results there as needed.

## Responses

- Use British spelling in prose and displayed text. Where the American spelling
  is also accepted in British English, use it (for example, optimization,
  minimize, normalized and equalization). Preserve code identifiers, API
  keywords, official titles and quotations.
- Do not use horizontal lines to separate entries in tables in your output.
- Never append generated follow-up links or action links. They are not rendered
  as functional links in the command-line interface used for this project and
  are therefore useless to the user.
- Prefer plain-text "pidgin math" to LaTeX notation in answers. Use formal
  typeset formulas only when plain-text notation would make the explanation
  materially less clear.
