# TODO

1. Clean up the README file(s) and setup/installation instructions to make it easier to set the package up after a fresh clone.
2. Clean junk from the repository.
3. Use uv rather than conda.
4. Translate to Icelandic.
5. Allow Swedish allocation.
6. Work on the optimal method to make it work and prevent cycling in some cases.
7. Allow displaying party abbreviations.
8. Improve input validation and error messages.
9. Remove debugging output, dead code, and obsolete commented-out blocks.
10. Consolidate repeated frontend table and form styling.

---
Other possible future work:
- Introduce an application version and release process.
  The historical Git tags, npm 1.0.0, and current code are not
  synchronized.

- Add continuous integration.
  Automatically run backend tests and the frontend build on every push.

- Add browser-level workflow tests.
  Cover loading votes, adding systems, calculating a single election, and
  running simulations.

- Clarify simulation terminology.
  Document fractional reference seat shares, scaling choices, and selected
  allocation comparators.

- Document and test the standalone Python interface.
  Cover single.py, noweb.py, method names, input paths, and expected
  output.

- Document election-data provenance and regeneration.
  Record sources, retrieval dates, transformations, and commands for
  rebuilding each dataset.

- Expand regression tests for statutory methods.
  Include known official election outcomes for Iceland, Norway, and
  eventually Sweden.

- Improve accessibility.
  Audit labels, tooltip-only explanations, keyboard navigation, table
  headings, and screen-reader behavior.

- Review numerical edge cases.
  Test zero-vote parties, zero-seat constituencies, exact thresholds, ties,
  overhangs, and convergence failures.
