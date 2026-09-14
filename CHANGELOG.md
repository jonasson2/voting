# Changelog

## 0.1.1 (unreleased)

- Update the README.md file and create a doc/deployment.md file.
- Add AGPL source notice in the help tab.
- Add a persistent HTTPS deployment using Waitress, systemd, and a reverse
  proxy, including `<host-url>/voting/` path support and `localhost:5001`.
  Remove several vulnerabilities by upgrading the Vue frontend.
- Various cleanup of unused files.
- Support fractional reference values in simulations.
- Move the party-vote basis control to the source settings and refine its behavior.
- Preserve pruned vote totals in a `Pruned` column and use them only when
  calculating percentage thresholds.
- When a national pruning cutoff would remove every party from a seat-bearing
  constituency, retain its largest local party (including exact ties).
- Preserve zero votes in election calculations, while treating them as one
  logical vote in generic adjustment methods, and remove forced allocation.
- Apply the Norwegian everywhere-standing rule using positive votes as its
  proxy and use ordinary Sainte-Laguë when locating Norwegian adjustment seats.
- Add Swedish national entitlement, overhang switching, and adjustment-seat
  allocation.
- Add election-law presets for Finland, Iceland, Norway, and Sweden.
- Add the Finnish 2019 and 2023 parliamentary elections as vote-table presets.

## 0.1.0

- Baseline version before pruned-vote tracking.
