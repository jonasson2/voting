# Recovered Loosemore-Hanby and Gallagher notes

Recovered from the uncommitted TODO.md recorded on 13 October 2026.
The measures described below were implemented in commit 76a244d; the original
planning text is retained for reference.

Superseded on 14 October 2026: Gallagher for lists and both regional indices
now measure within-unit party proportionality, with seat-weighted averaging.
The geographical constituency Gallagher measure is removed. See measures.md
for the current definitions.

## Add geographical proportionality measures

Implement three additional measures:

- `lh_regions`: “Loosemore-Hanby index for regions (%)”
- `gallagher_regions`: “Gallagher index for regions (%)”
- `gallagher_constituencies`: “Gallagher index for constituencies (%)”

Retain the existing `lh_constituencies` measure. Together these provide
Loosemore-Hanby and Gallagher at both geographical levels.

### Definitions and benchmark

For geographical unit g (a constituency or region), define:

    v[g] = valid votes in g / valid votes in all geographical units
    s[g] = final seats in g / final seats in all geographical units
    Loosemore-Hanby (%) = 100 * 0.5 * sum(abs(s[g] - v[g]))
    Gallagher (%) = 100 * sqrt(0.5 * sum((s[g] - v[g])**2))

Use ALL valid constituency votes, including votes for parties receiving no seats
and pruned votes. Reuse `Simulation.constituency_vote_totals` so the benchmark
matches existing constituency Loosemore-Hanby. Use final geographical seat totals
including fixed AND adjustment seats, rather than the input seat budgets.
National-list seats without a geographical assignment and separate national
party-vote totals are excluded from these geographical shares.

For regions, aggregate constituency votes and seats within each region FIRST,
then calculate shares and the index. Do not average constituency indices or
apply an additional population, party-seat, or region-size weight.

These measures compare geographical seat totals with geographical vote totals;
they do NOT measure proportionality between parties within regions, or the
geographical distribution of each party's seats. The benchmark is votes, not
population or statutory area-weighted entitlements. Deliberate rural advantages
therefore count as deviations from this benchmark. Lower is better; zero means
exact proportionality. Loosemore-Hanby has the interpretation of the share of
seats needing geographical redistribution, ignoring integer rounding. Gallagher
gives more weight to large individual discrepancies.

Use shares between 0 and 1 internally, consistent with `lh_constituencies`, and
register percentage formatting exactly once. Do not display the raw squared
sum, omit the square root, or multiply by 100 twice. Regions/constituencies with
zero votes or zero seats remain included when overall totals are positive.
When overall votes or geographical seats are zero, return 0 consistently with
the existing geographical Loosemore-Hanby zero-total convention.

### Availability and integration

- Both regional indices appear ONLY when the source vote table explicitly
  defines valid regions. Follow the same mapping, transformation handling,
  and web/export availability rules specified above for regional spread.
  One explicit region is valid and gives both regional indices zero.
- Constituency Gallagher is available without regions. Add all available new
  rows to the default “Geographical balance” quality-measure group beside
  existing constituency measures; supply concise definition tooltips.
- Reuse or generalize the existing geographical calculation in
  `backend/simulate.py` (`reference_measures`, `geographical_seat_displacement`,
  `constituency_vote_totals`) without changing `lh_constituencies` values.
- Wire registration, statistics, web display, offline CSV, spreadsheet exports,
  parallel aggregation, and saved/reloaded results through the existing paths
  described above. Calculate indices per replicate before normal aggregation;
  do not calculate Gallagher from averaged regional/constituency shares.
- Update `measures.md` with formulas, units, benchmarks, and availability.

### Acceptance checks

1. Vote shares (0.6, 0.4) and seat shares (0.55, 0.45) give both indices 5%.
2. Vote shares (0.5, 0.3, 0.2) and seat shares (0.6, 0.25, 0.15) give
   Loosemore-Hanby 10% and Gallagher approximately 8.660254%. This distinguishes
   Gallagher from Loosemore-Hanby and tests the square-root normalization.
3. Exact proportionality gives zero. Test zero-vote and zero-seat units, overall
   zero totals, and inclusion of votes for parties without seats/pruned votes.
4. Group constituencies into regions and verify indices are calculated from
   aggregated totals. Discrepancies within a region can cancel: equal votes in
   four constituencies with seat shares (0.3, 0.2, 0.3, 0.2), grouped as the first
   two and last two, give regional indices zero but positive constituency indices.
5. Without regions, omit both regional rows from web/export results while
   retaining constituency Gallagher and existing constituency Loosemore-Hanby.
   Verify regional rows appear for any allocation method when regions exist.
6. Check existing constituency Loosemore-Hanby results remain unchanged; test
   percentage formatting, replicate aggregation, and offline CSV integration.
   Follow repository verification instructions when implementing these changes.
