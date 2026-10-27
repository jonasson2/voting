# Simulation quality measures: display redesign

Implemented design for the simulation quality-measure display. The default
display contains core measures, with optional rows selected by checkboxes.

## Core measures

Show these by default in one continuous table, with electoral systems in columns
and measures in rows. Remove both existing headings:

- “Differences between allocated and fractional reference seat shares, summed
  over constituency lists”.
- “Specific quality indices for allocations in the constituencies”.

Each row should have a name that makes sense without those headings. Keep means
and 95% confidence intervals. Explain formulas and reference scaling in tooltips.

Core measure inventory (display order follows the sections below):

1. Loosemore-Hanby index for lists.
   Also Gallagher index for lists, and regional Loosemore-Hanby and Gallagher
   when regions are defined.
2. Entropy score.
3. Local squared deviation per reference seat.
4. Total list seat deviation.
5. Maximum seat surplus.
6. Maximum seat shortfall.
7. Maximum seat-share surplus.
8. Maximum seat-share shortfall.
9. Constituency disparity.
10. Loosemore-Hanby index for constituencies.
11. Loosemore-Hanby index for parties.
12. Maximum party-seat surplus.
13. Maximum party-seat shortfall.

### Display sections

The shared catalogue now organizes output into these blocks:

- **List allocation quality measures:** Constituency measures and Quotient optimality.
- **Total allocation quality measures:** Geographical balance and Party totals.
- **Additional proportionality measures** (`show_additional`): the four extra
  local proportionality measures under Constituency measures, and total squared
  party-seat deviation under Party totals. When `show_scalings` is also checked,
  include the four extra measures for each of double, party and national scaling
  here, in their own scaling subblocks.
- **Double, party, and national scaling** (`show_scalings`): one subblock for
  each of these scalings, containing the five seat-deviation measures.
- **Specifically for single-seat constituencies** (`show_single_seat`): Local
  measures (slope, correlation, maximum negative margin and constituency count)
  and Party totals (total excess and potential overhang).
- **System comparison**, **Sensitivity**, and **Single-list sensitivity** retain
  their existing subblocks when applicable.

Each output block has its own title, system header and separating space.
Checkboxes affect completed web and CSV display. Excel includes all optional
measures, organized into the same blocks and subblocks; its existing extra
diagnostics remain in a Supplementary diagnostics block. Catalogue metadata
defines the quality/comparison block boundaries for all three reports.

Organize the display in this order:

1. **Constituency measures:** Loosemore-Hanby and Gallagher indices for lists,
   the corresponding regional party-proportionality indices when regions exist,
   and local squared deviation per reference seat. Always include
   total list seat deviation and the four list surplus/shortfall maxima here.
   These all compare with local fractional seats: constituency seat count
   multiplied by the list's local vote share. Do not split the constituency measures
   into separate proportionality and seat-deviation blocks.
2. **Quotient optimality:** entropy score and, when comparing multiple systems,
   entropy relative to system 1, immediately after Constituency measures,
   before the double-scaling block. Entropy is closely related to biproportional
   allocation, but uses the feasible quotient-product optimum rather than
   doubly scaled fractional seats as its benchmark. Display it once,
   independently of the scaling display option.
3. **Measures with double scaling:** total list seat deviation and the four
   list surplus/shortfall maxima, using doubly scaled fractional seats.
4. **Measures with party scaling**, then **Measures with national scaling:**
   the same five measures using the corresponding fractional seats.
5. **Geographical balance:** constituency disparity and Loosemore-Hanby index
   for constituencies.
6. **Party totals:** Loosemore-Hanby index for parties, maximum party-seat
   surplus, and maximum party-seat shortfall.

Always show Constituency measures. Show the double, party, and national blocks together
when “Double, party, and national scaling” is checked.
Use “fractional seats” for the potentially noninteger benchmark seat counts;
“seat shares” denotes proportions of seats.

### Table layout and settings controls

- Put section titles in a new first column, followed by the measure-name column
  and the electoral-system columns. Show each section title once beside its
  group of rows. Split the longest titles over two lines. Start with this layout
  and review its readability before considering another presentation.
- Keep the current sensitivity-analysis output unchanged for now.
- Below “Calculate entropy score”, add a separate horizontal divider and then
  a “Show additional measures” area containing three checkboxes, in order:
  “Additional proportionality measures”, “Double, party, and national scaling”,
  and “Specifically for single-seat constituencies”. This area controls display,
  not calculation.
- Use checkboxes instead of Yes/No selectors for boolean options, including
  threshold use, entropy calculation, sensitivity calculation, and the optional
  display groups. Remove the separate Reference seat scaling selector.
- Compute and retain the optional quality measures regardless of their display
  selections, so showing them does not require rerunning a simulation. Ordinary
  quality measures are already collected in the current implementation;
  entropy and sensitivity remain separately controlled calculations.

Decision: move both party-seat maxima into the core, so the national party
section shows the overall discrepancy and the worst surplus and shortfall.
The optional “Additional proportionality measures” checkbox adds rows to their
corresponding sections, rather than creating a separate output section:

- Total squared party-seat deviation goes into Party totals.
- Total squared list seat deviation (Hare quota), maximum relative
  over-representation (D'Hondt),
  and total absolute deviation per reference seat go into Constituency measures and
  the other scaling blocks when displayed.

### Local allocation discrepancies

For a constituency–party list, let s be allocated seats and q its fractional
reference allocation. Define surplus = max(s - q, 0) and shortfall = max(q - s, 0).
“Shortfall” is proposed as the label for what we have also called “shortage”.

| Proposed row name | Definition / purpose | Status |
| --- | --- | --- |
| Total list seat deviation | Full sum of abs(s - q) across constituency lists | Core; report in seats, without division by two |
| Loosemore-Hanby index for lists | Half the absolute-deviation sum across constituency lists, divided by total seats; local vote-share references | Core; report as a percentage |
| Maximum seat surplus | Largest surplus for any constituency–party list | Proposed core; raw seats |
| Maximum seat shortfall | Largest shortfall for any constituency–party list | Proposed core; raw seats |
| Local squared deviation per reference seat | Sum of (s - q_local)^2 / q_local over constituency lists, with q_local defined from local vote shares | Core; constituency errors weighted by seat count |

The former `sum_abs` measure reported half the absolute-deviation sum, despite
its name “Absolute values (Hare quota)”. When the reference and allocated seat
totals match:

    total surplus = total shortfall = half the total absolute deviation

Decision: omit separate raw total seat surplus and total seat shortfall rows.
The reference scaling distributes the same total seats as the actual allocation,
so these totals contain no additional information beyond the absolute-deviation
sum. Retain the deviation row and both maxima.

Decision: retain “Total list seat deviation” as the full absolute-deviation sum
in seats, and also include “Loosemore-Hanby index for lists”, using the classical
half-sum normalization and reporting a percentage:

    100 × sum over constituency lists of abs(s - q_local) / (2 × total seats)

Here q_local uses within-constituency vote shares. The measure does not follow
the general reference-scaling setting. A version using two-way references would
need a different, qualified label.

This equals the constituency-seat-weighted average of the local indices.
No tooltip wording is needed at this design stage.

### National party proportionality

Include **Loosemore-Hanby index for parties**, **Maximum party-seat surplus**,
and **Maximum party-seat shortfall** in the core. Define each party's reference
seats as its national vote share times
the total number of seats:

    100 × sum over parties of abs(allocated seats - reference seats)
        / (2 × total seats)

Both Loosemore-Hanby measures use the classical half-sum normalization and are
reported as percentages; lower is better. The party index uses national vote
shares independently of the general reference-scaling setting.

The existing “Maximum seat-share surplus” and “Maximum seat-share shortfall”
divide each list's surplus or shortfall by its constituency's final seat count.
They are proportions, not raw seat counts. Decision: retain both seat-share
maxima alongside the raw seat maxima for now. Corresponding totals of
these normalized discrepancies would be another possible definition of the
total surplus and shortfall rows; they would need explicit seat-share labels.

The per-reference-seat absolute-deviation sum is different: each term is divided
by q, not by the constituency seat count, and the current sum is not halved.
Directional per-reference-seat sums could remain secondary measures.
Decision: move “Total absolute deviation per reference seat” into the optional
additional-proportionality group. It uses sum of abs(s - q) / q. Each
positive-reference zero-seat list contributes 1; large relative surpluses can
still identify weakly supported seat placements, whether avoidable or forced.

### Local Sainte-Laguë measure and candidate methods

Decision: include the seat-weighted generalized Sainte-Laguë objective in the
core. For constituency c with N_c total seats (fixed plus adjustment), define:

    q_local = N_c × list votes / constituency vote total
    E_c = sum over parties of (s - q_local)^2 / q_local
    E = sum over constituencies of E_c

Lower is better. The normalized local error E_c / N_c is weighted by N_c, so
the overall objective weights constituencies by their seat counts. No additional
factor N_c is applied to E_c. Retain the raw sum E, rather than an optimum-relative
score, so matched systems can be compared against the same local benchmark.

This measure always uses within-constituency reference shares, independently of
the general reference-scaling setting. It is the existing `sum_sqshare` formula
when that setting is “within constituencies”. Reuse that calculation and avoid
duplicate rows; if a version using two-way references is also displayed, label
the benchmarks explicitly. For q_local = 0, a zero allocation contributes zero;
a positive allocation has an infinite penalty.

Implemented methods (19 October 2026), with provisional names:

- **Seat-share optimization (LP)** (`seat-share-lp`): minimize cumulative
  marginal costs `d(k) / q_local`, subject to prescribed constituency and party
  totals and protected fixed seats. The increasing seat costs permit an exact
  continuous network LP, sharing the solver machinery with Optimal LP.
- **Seat-share switching** (`seat-share-switching`): start by selecting the
  largest available `q_local / d(k)` while respecting the totals, then choose
  the reciprocal two-constituency exchange giving the greatest additive cost
  reduction. Pairwise switches alone need not reach the global optimum. If
  zero-vote lists cause a greedy dead end, a feasibility LP supplies a starting
  allocation before switching.

Both require prescribed final constituency totals: flexible adjustment seats
are excluded. The adjustment-seat rule remains selectable and determines
`d(k)`; the fixed-seat and national party-total rules remain independent.
With Sainte-Laguë, cumulative cost is `sum(s²/q_local)`, equal to E plus the
constant total number of seats. With D'Hondt, cumulative cost is
`sum(s(s+1)/(2q_local))`. This is a generalized D'Hondt objective, rather than a
claim that it minimizes maximum relative over-representation under arbitrary
multi-constituency constraints. Other supported divisor rules work in the same
way. No additional weighting factor is applied: the seat weighting remains the
agreed choice. Equal constituency and equal voter weighting are not separate
methods.

Use actual fractional votes without a one-vote floor. Zero-reference lists
cannot receive seats in these methods; incompatible protected seats or totals
produce an explicit error rather than silently changing that convention.
The methods work with prescribed regional party totals when regions are used.
Their entropy score retains its ordinary quotient-product definition; an exact
optimum of this additive objective need not have an entropy score of 100%.

Derivation and the three weighting alternatives are described in
[generalized-sainte-lague.md](/Users/jonasson/drive/kosningagrein/notes/generalized-sainte-lague.md).

### Ricca et al. methods

Implemented under Optimal methods as RSSS MinL1 and RSSS MinL2, each with
a separate constituency scaling or double scaling choice. Only the absolute objectives are
offered; the relative versions, MinMax and MinMaxLexBest are not included.
Both methods use the network LP with prescribed constituency totals and
protected fixed seats. Their objectives do not use the adjustment divisor or
extra constituency weights. The method's scaling is independent of the
reference scaling selected for quality-measure display.

| Method | Absolute deviations | Relative deviations |
| --- | --- | --- |
| MinL1 | `sum abs(s-q)` | `sum abs(s-q)/q` |
| MinL2 | `sum (s-q)^2` | `sum (s-q)^2/q^2` |
| MinMax | `max abs(s-q)` | `max abs(s-q)/q` |

Here s is a list's allocated seats and q its fractional reference seats.
The paper allows constituency-scaled or doubly scaled q. Compare its methods
using constituency-scaled q with our GSL, which minimizes `sum (s-q)^2/q`.
The paper discusses relative deviations in section 9; its Italian-election
comparisons use absolute deviations and doubly scaled q.

### Switching approximations

The approximation family offers Entropy switching, Seat-share switching,
RSSS MinL1 switching and RSSS MinL2 switching. Switching+ has been removed;
Entropy switching uses the former Flexible switching method (`switching-flex`).

All four share an improvement engine. It chooses the reciprocal two-party,
two-constituency exchange with the largest objective improvement. Entropy
switching additionally considers moving one party's seat between constituencies
within their bounds. Fixed seats and the starting party totals are preserved.
Only strictly improving moves are accepted; longer cycles can still improve
an allocation after the algorithm stops.

Entropy maximizes the quotient product (computed through its logarithm).
Seat-share minimizes `sum [d(1)+...+d(s)]/q` for the chosen divisor sequence.
Both retain the full divisor selector. RSSS switching uses the same `q` and
absolute MinL1 or MinL2 objective as its exact counterpart, with a separate
constituency/double scaling choice and no divisor dependence.

Seat-share and RSSS switching require prescribed constituency totals; their
reference seats remain fixed during switching. Flexible reference-seat
objectives need a separate decision before those methods can support flexible
totals. Greedy starting allocations use quotient scores (Entropy and Seat-share)
or minimum marginal costs (RSSS). Seat-share and RSSS fall back to a feasibility
LP if sparse votes prevent greedy completion. Reports show the initial
allocation and each improving exchange, with its objective reduction (or
log-product increase for Entropy).

### Other core measures

| Row name | Purpose |
| --- | --- |
| Entropy score | Quotient-product quality relative to the feasible optimum for the system; 100% is optimal |
| Loosemore-Hanby index for constituencies | Half the absolute deviation from vote-proportional constituency seat totals, divided by total seats; report as a percentage |
| Constituency disparity | Highest constituency votes per seat divided by lowest; 1 means equality |

Decision: replace the raw geographical measure (previously “Geographical seat
displacement”, then proposed as “Total constituency seat deviation”) with
“Loosemore-Hanby index for constituencies”. For constituency c:

    reference seats_c = total seats × constituency votes_c / national votes
    index (%) = 100 × sum_c abs(allocated seats_c - reference seats_c)
                    / (2 × total seats)

Use total final constituency seats, including fixed and adjustment seats, and
all constituency votes, including pruned votes. This normalization supports
comparisons between countries with different parliament sizes. The benchmark
is votes, rather than population. Do not retain a second raw geographical row
in the core.

Core measure: **Entropy relative to system 1**. This is useful
for matched comparisons of flexible and fixed constituency seat counts, where
individual entropy scores have different feasible optima. Show it in Quotient
optimality as a quotient-product ratio (system 1 equals 1), not a percentage.
Do not add a separate entropy-difference measure.

### Dependence on allocation method and reference scaling

The following describes the proposed display, including measures whose new
normalizations or dedicated local references are not yet implemented. Compare
the same votes and the same electoral-system settings, changing only the
adjustment-seat allocation method or the reference-scaling option.

| Core measure | Independent of adjustment-seat allocation method? | Independent of reference scaling (within constituencies versus both)? |
| --- | --- | --- |
| Total list seat deviation | No | No |
| Loosemore-Hanby index for lists | No | Yes; always local references |
| Loosemore-Hanby index for parties | Yes, if national party totals are unchanged | Yes; always national vote-share references |
| Maximum party-seat surplus | Yes, if national party totals are unchanged | Yes; always national vote-share references |
| Maximum party-seat shortfall | Yes, if national party totals are unchanged | Yes; always national vote-share references |
| Maximum seat surplus | No | No |
| Maximum seat shortfall | No | No |
| Maximum seat-share surplus | No | No |
| Maximum seat-share shortfall | No | No |
| Local squared deviation per reference seat | No | Yes; always local references |
| Entropy score | No | Yes |
| Loosemore-Hanby index for constituencies | Yes, if constituency seat totals are unchanged | Yes |
| Constituency disparity | Yes, if constituency seat totals are unchanged | Yes |

Ordinary placement methods with the same prescribed national party totals have
the same party index. Methods that do not enforce those totals, or otherwise
change them, need not. Similarly, fixed constituency seat totals make both
geographical measures independent of how seats are placed among parties;
flexible constituency totals can make both depend on the allocation method.

Reference scaling changes a measurement benchmark, not the election allocation.
The local and national references explicitly required by the Loosemore-Hanby
indices and the local squared-deviation measure override that display setting.

## Optional groups

Use independent checkboxes to show or hide whole groups. Proposed default: core
visible, optional groups unchecked. Avoid duplicate rows except for the agreed
repeat of Total list seat deviation: keep its constituency-scaled row in the
core and include all four reference scalings in Additional proportionality
measures. Those four additional rows appear whenever Show additional measures
is checked, independently of the Double, party, and national scaling checkbox.
Other additional measures for the three non-constituency scalings continue to
require both checkboxes.

### Specifically for single-seat constituencies

The requested starting point is the last six measures in the current third block:

| Current measure | Display decision |
| --- | --- |
| Slope of seat excess regressed on reference seat shares | Candidate |
| Correlation of seat excess and reference seat shares | Candidate |
| Total seat excess | Candidate; needs a clearer name identifying the national integer reference |
| Maximum negative margin over constituencies | Candidate; needs an explanatory name or tooltip |
| Frequency of negative margin over constituencies | Candidate; clarify that the current value counts constituencies |
| Potential overhang | Candidate |

Decision: label this optional group “Specifically for single-seat constituencies”.
This identifies its intended focus, rather than a mathematical restriction:
several of these diagnostics also apply to multi-seat constituencies. Choose
all six or a useful subset.

In particular, current “Total seat excess” is not the proposed local total seat
surplus. It compares national party totals with an integer national reference
allocation. Keep those concepts distinct.

### Additional proportionality measures

This optional selection combines named-method measures, the relative absolute-
deviation measure, and squared party-total deviation. Together with the
single-seat-constituency group, this gives two selectable optional groups.
Display its rows in the corresponding list and party sections, not in a
separate additional-measures section.

Decision: retain the unweighted absolute-deviation measure in the core. Put
maximum relative over-representation in this optional group. The local
generalized Sainte-Laguë squared-deviation measure remains core; its membership
in this group should not create a duplicate row. The unweighted squared-deviation
measure remains optional.
Both unweighted absolute and squared
deviation are minimized by Hare with largest remainders in a single constituency;
the squared measure additionally emphasizes large discrepancies.

Include measures currently marked with a named minimizing method in parentheses.
The characterization applies to an ordinary single-constituency allocation;
additional constraints in a multi-constituency system can change what is optimal.

| Proposed self-contained name | Current measure / method |
| --- | --- |
| Total squared list seat deviation (Hare quota) | `sum_sq` |
| Maximum relative over-representation (D'Hondt) | `max_overrepresentation` |
| Total absolute deviation per reference seat | `sum_absshare`; depends on both allocation method and reference scaling |
| Total squared party-seat deviation | National party-total squared deviation; independent of local reference scaling |

Hare's absolute-deviation measure overlaps with the core. Avoid duplicate rows.
Maximum relative under-representation is removed from all reports and from the
collected measures. It reaches 1 whenever a positive-reference list receives no
seats, which makes it uninformative in many of our applications.
Decision: remove “Squared values per allocated seat” entirely, including from
the optional named-method group. Its Hill–Huntington interpretation requires
positive allocations for positive-reference lists; zero-seat lists are routine
in our applications. A mathematically faithful infinite penalty would make the
measure unhelpful, and a finite replacement would lose that interpretation.

The two party-seat maxima are core measures alongside the party index; squared
party-seat deviation is optional. Present the current signed minimum as a
positive maximum shortfall.
Retain the former Under-allocation per reference seat in Excel only, renamed
**Total relative seat shortfall**, for each reference scaling:

    sum over lists(max(q - s, 0) / q), for q > 0

Zero-reference lists contribute zero. The Excel comment must explain that every
unrepresented positive-reference list contributes 1, regardless of its size.
The measure is dimensionless, not a count of missing seats. Its calculation is
unchanged. Over-allocation per reference seat and the secondary squared-deviation
measures also remain Excel-only.

## Reference scaling and outputs

- Party and double scaling use the integer national party targets passed to
  list allocation, including thresholds, the national allocation rule,
  protected fixed seats and any country-specific recalculation. Individual
  reference list seats remain fractional. Double scaling also preserves final
  constituency totals; with separate national seats, constituency party totals
  are capped at the integer targets and the remainder forms the national reference.
  National scaling and the dedicated national party-proportionality measures
  retain their fractional vote-share benchmarks.
- Always compute and accumulate all four reference scalings and their optional
  measures. Constituency measures remain visible; one checkbox shows the double, party,
  and national blocks together. It changes completed results immediately without
  rerunning. Repeat total list seat deviation and the four list surplus/shortfall
  maxima in each block, along with enabled optional list measures. Keep the
  dedicated local indices and entropy score as single rows. Scaling display
  choices do not affect allocation or sensitivity; calculate sensitivity once
  per replicate.
- Use proportions for seat-share discrepancies, not percentages or percentage
  points. Entropy score, all Loosemore-Hanby indices and Gallagher indices use
  percentages.
- Optional-group selections also control CSV output. Web, CSV and Excel use one
  shared catalogue; Excel always includes the optional and secondary measures.
- Retain secondary measures in Excel, with clear names and definitions, even when
  omitted from the default web display. Pruning the display need not remove the
  underlying statistics.
- System-comparison tables are separate from this proposed core/optional-group
  redesign. Keep the current sensitivity-analysis output unchanged for now.

## Design decisions completed

The former decisions on maxima, optional squared party-seat deviation,
secondary relative-deviation measures and entropy relative to system 1 are
complete. Current follow-up work is recorded in [TODO.md](TODO.md).

The implementation uses one shared measure catalogue for names, groups and
output selection rather than separate web and CSV lists.

## Implementation choices

- New simulations compute all four scalings. New saved settings use the boolean
  `show_scalings` instead of `scaling`. Loading older settings with any nonlocal
  scaling enables the new display checkbox unless an explicit `show_scalings`
  value is present.
- All three optional display selections default to unchecked. Toggling them changes
  the displayed completed results immediately; it does not change calculation.
- All six single-seat diagnostics are retained. Their reference-dependent rows
  and Excel's detailed reference matrices always use constituency scaling in new runs. The
  benchmark is identified in the diagnostic labels and report settings.
- Scaling statistics have separate identifiers for each benchmark. Seat
  allocation and sensitivity run once per replicate, not once per scaling.
- Infinite relative penalties are retained through statistics files and merging,
  displayed as infinity with unavailable SD/CI rather than finite substitutes.
- CSV uses separate section and measure fields; each average and confidence
  interval remains one cell. Excel retains secondary measures and cell comments.

Each electoral-system Excel sheet includes Double scaled reference seat shares
immediately to the right of Reference seat shares. Store per-replicate matrices
using the already computed double-scaling benchmark, so means and standard deviations are computed before export, rather than by scaling
averaged votes. Include source-vote values, national rows and totals when
applicable. Statistics files use format version 2; earlier formats are not
supported. Minimum and maximum replicate summaries are neither accumulated
nor included in Excel reports or saved statistics.

## Geographical balance and adjustment-seat spread

Local proportionality indices compare parties' vote and final seat shares
within each constituency. For unit u, let v[u,p] and s[u,p] be the within-unit
vote and seat shares of party p, and S[u] its final seat total:

    LH[u] = 0.5 * sum over parties(abs(s[u,p] - v[u,p]))
    Gallagher[u] = sqrt(0.5 * sum over parties((s[u,p] - v[u,p])**2))
    reported index = sum over units(S[u] * index[u]) / sum over units(S[u])

“Gallagher index for lists (%)” uses constituencies as units. The existing
“Loosemore-Hanby index for lists (%)” is equivalent to the seat-weighted local
LH average. Both use retained parties after pruning, and final fixed plus
adjustment seats; separate national-list votes and seats are excluded.

“Loosemore-Hanby index for regions (%)” and “Gallagher index for regions (%)”
first aggregate each party's votes and final seats across constituencies in
its region, then compute within-region party shares and average the regional
indices weighted by regional seats. Both appear under Constituency measures only
when the source defines valid regions. A single region measures national
party proportionality and need not give zero. Invalid transformed geography
is displayed as unavailable. These measures are independent of reference
scaling. Zero-seat units have zero weight; zero-vote units contribute zero.
All indices use proportions internally and are displayed as percentages.

Geographical balance retains constituency disparity, constituency
Loosemore-Hanby, and adjustment-seat spread. Constituency Loosemore-Hanby
compares constituency shares of national valid votes and final constituency
seats, includes pruned votes, and excludes national-list votes and seats.
The former geographical Gallagher and regional geographical Loosemore-Hanby
measures have been removed. The new local indices have separate statistics keys from the removed
geographical measures.

Adjustment-seat spread across constituencies counts, for each party, the
constituencies receiving at least one of its adjustment seats. Regional spread
counts distinct recipient regions. Weight each party's count by its total
seats, including national-list seats, and divide by total seats across parties.
Parties without adjustment seats contribute zero to the numerator but retain
their seat weight in the denominator. Zero total seats gives zero spread. Both
measures are decimal weighted averages of counts; larger means wider spread.
Regional spread follows the same regional availability rule as the indices.

The Entropy score is the allocation quotient product divided by the maximum
achievable under the system's rules and constraints. Its global optimum may
change intermediate party-by-region totals while retaining genuine regional
seat budgets, national party targets, protected seats and constituency bounds.
