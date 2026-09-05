## Model scope

The Voting simulator supports statutory, comparative, and hypothetical applications
of allocation algorithms.

Do not enforce a country's complete legal seat structure merely because a method is
named after that country. For example, `norwegian-law` may be used with zero, one,
or several adjustment seats per constituency. 

## Changes

- Add or update focused regression tests for allocation and input-handling bugs.
- Run `python test.py` from `backend/` after backend changes.
- Keep parsers and generated election data under `data/` and record sources in
  `data/sources.txt`.
