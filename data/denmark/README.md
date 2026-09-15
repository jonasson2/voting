# Danish Election Data

The 24 March 2026 mainland vote file is available in the simulator's presets.
Select it in tab 1, then select the Denmark election-law preset in tab 2.
Faroe Islands and Greenland are excluded.

From the repository root:

```sh
uv run --locked python data/denmark/get-votes.py 2026
```

Add `--refresh` to download sources again. Downloads are retained in
`raw/2026/` (ignored by Git), including the official allocation report.
The script writes `data/denmark_2026.csv` and `official-results_2026.json`.
The latter preserves official votes and fixed/adjustment seats nationally,
by region, and by constituency for regression tests. Sources are listed
in `data/sources.txt`.

## Vote File Format

The file uses UTF-8 and comma-separated fields, with every row padded to
the header's width. CSV quoting preserves names containing commas.

- Header: table name, `fixed`, `min_adj`, `max_adj`, `region`, then party and
  independent-candidate abbreviations.
- `Party names`: names aligned with the party/candidate columns; other fields
  are blank.
- `Independent candidates`: `1` for an independent and `0` for a party,
  aligned with the vote columns; other fields are blank.
- `Max adj seats`: the national adjustment-seat count (40) in the `max_adj`
  column; other fields are blank.
- Constituency rows: official fixed-seat counts, minimum adjustment seats 0,
  unlimited maximum (`-`), region abbreviation, and unmodified vote counts.
- After a blank row, `Regions,Name,adj` begins the region table. Its rows hold
  abbreviation, official region name, and adjustment-seat count.

The region identifiers `H`, `SS`, and `MN`, and independent identifiers
`U1` to `U6`, are local labels. Party letters and all names come from the
official results. No parties or independents are pruned, and no votes are
added. Faroe Islands and Greenland are outside this Danish allocation.

## Checks

`national-results_2022.json` records the official national overhang example
from tables 1 and 3 of the linked 2022 report. It is a small hand-transcribed
regression fixture, not a full election preset.

The backend tests reproduce every official 2026 constituency and region
allocation, and the 2022 overhang totals. Danish simulations omit independent
candidates, retain their votes in Pruned, and give participating lists at
least one vote. Single elections use unmodified votes. If absent parties
prevent regional allocation, the simulator reports an error: the statutory
advance-allocation procedure remains deferred.

The generator checks each constituency's valid-vote total, individual
independent votes, and every party's votes and seats against the region and
national totals. It also checks the 2026 counts of regions, constituencies,
parties, independent candidates, votes and seats.

```sh
uv run --locked python -m unittest discover -s data/denmark -p 'test_*.py'
```
