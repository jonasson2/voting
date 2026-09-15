# Development workflow

Changes may be proposed and completed one amendment at a time. There is no need
to provide a complete list in advance.

For each amendment:

1. Begin from a reviewed, tested, and committed checkpoint.
2. Establish the exact intended behaviour and clarify only material ambiguity.
3. Identify the affected inputs, outputs, invariants, and implementation layers.
4. Implement one complete change from input through output, with focused
   regression tests. Small related cosmetic changes may be grouped, but
   allocation changes should normally remain separate.
5. Represent election laws through explicit, general system settings rather
   than country-name checks.
6. Keep parsing, validation, allocation, and presentation separate. Prefer
   existing data objects to growing argument lists, avoid chains of boolean
   parameters, and extract shared code only when operations are genuinely the
   same.
7. Remove obsolete paths instead of adding compatibility scaffolding unless
   compatibility is actually required.
8. Review the resulting diff for duplication, oversized functions, growing or
   unclear signatures, misplaced country-specific logic, dead branches, and
   inconsistent frontend and backend defaults.
9. Run focused tests while developing. Before a checkpoint, run `python test.py`
   from `backend/`, the frontend tests and build, and relevant browser checks.
10. Commit before beginning the next substantial amendment.

Use an ignored note under `tmp/` only when a change leaves a deferred question
or dependency that must survive between sessions.
