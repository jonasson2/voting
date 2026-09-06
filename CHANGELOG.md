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

## 0.1.0

- Baseline version before pruned-vote tracking.
