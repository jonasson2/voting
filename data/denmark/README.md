# Danish Election Data

The 5 June 2019, 1 November 2022, and 24 March 2026 mainland vote files are
available in the simulator's presets. Select one in tab 1, then select the
Denmark election-law preset in tab 2.
Faroe Islands and Greenland are excluded.

From the repository root:

```sh
uv run --locked python data/denmark/get-votes.py 2022
```

Add `--refresh` to download sources again. Downloads are retained in
`raw/YEAR/` (ignored by Git), including the official allocation report when
available.
The script writes `data/denmark_YEAR.csv` and `official-results_YEAR.json`.
The JSON snapshot preserves the downloaded official data. The 2019 and 2022
result pages publish votes but not seat tables, so their constituency fixed-seat
counts and regional adjustment-seat counts come from the linked official
allocation reports. Sources are listed in `data/sources.txt`.

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

`national-results_2022.json` records the official recalculation of national
party totals from tables 1 and 3 of the linked 2022 report. It is a small
hand-transcribed regression fixture, not a full election preset.

The backend tests reproduce every official 2026 constituency and region
allocation, and the 2022 recalculated party totals. Danish simulations omit
independent candidates, retain their votes in Pruned, and give participating lists at
least one vote. Single elections use unmodified votes. If absent parties
prevent regional allocation, the simulator reports an error: the statutory
advance-allocation procedure remains deferred.

The generator checks each constituency's valid-vote total, individual
independent votes, and every party's votes and seats against the region and
national totals when the result pages publish seats. For 2019 and 2022, the
official allocation report supplies fixed-seat counts by constituency and
adjustment-seat counts by region. It also checks the counts of regions,
constituencies, votes, fixed seats and adjustment seats.

```sh
uv run --locked python -m unittest discover -s data/denmark -p 'test_*.py'
```
