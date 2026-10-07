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

Organize the display in this order:

1. **Local measures:** Loosemore-Hanby index for lists and local squared
   deviation per reference seat. When local scaling is selected, also include
   total list seat deviation and the four list surplus/shortfall maxima here.
   These all compare with local fractional seats: constituency seat count
   multiplied by the list's local vote share. Do not split the local measures
   into separate proportionality and seat-deviation blocks.
2. **Quotient optimality:** entropy score and, when comparing multiple systems,
   entropy relative to system 1, immediately after Local measures,
   before the double-scaling block. Entropy is closely related to biproportional
   allocation, but uses the feasible quotient-product optimum rather than
   doubly scaled fractional seats as its benchmark. Display it once,
   independently of the selected scalings.
3. **Measures with double scaling:** total list seat deviation and the four
   list surplus/shortfall maxima, using doubly scaled fractional seats.
4. **Measures with party scaling**, then **Measures with national scaling:**
   the same five measures using the corresponding fractional seats.
5. **Geographical balance:** constituency disparity and Loosemore-Hanby index
   for constituencies.
6. **Party totals:** Loosemore-Hanby index for parties, maximum party-seat
   surplus, and maximum party-seat shortfall.

Show scaling-dependent rows and blocks only for the selected scalings. The
dedicated local indices remain visible independently of those selections.
Use “fractional seats” for the potentially noninteger benchmark seat counts;
“seat shares” denotes proportions of seats.

### Table layout and settings controls

- Put section titles in a new first column, followed by the measure-name column
  and the electoral-system columns. Show each section title once beside its
  group of rows. Split the longest titles over two lines. Start with this layout
  and review its readability before considering another presentation.
- Keep the current sensitivity-analysis output unchanged for now.
- Below “Calculate entropy score”, add a separate horizontal divider and then
  a “Show additional measures” area containing the two optional-group
  checkboxes: “Additional proportionality measures” and “Specifically for
  single-seat constituencies”. This area controls display, not calculation.
- Use checkboxes instead of Yes/No selectors for boolean options, including
  threshold use, entropy calculation, sensitivity calculation, and the optional
  display groups. The four reference-scaling choices are also independent
  checkboxes, as described below.
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
  over-representation (D'Hondt), maximum relative under-representation (Adams),
  and total absolute deviation per reference seat go into Local measures and
  the other scaling blocks for each selected reference scaling.

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

Possible future methods, not yet approved for implementation:

- Exact generalized Sainte-Laguë: minimize E using its LP formulation, subject
  to prescribed constituency and party totals and protected fixed seats.
- A switching approximation: preserve those constraints and choose exchanges
  that reduce E, using additive marginal costs (2k - 1) / q_local. Pairwise
  switches alone need not reach the global optimum.

The seat weighting is the preferred choice for these candidates. Equal
constituency and equal voter weighting need not become separate methods now.
Review and prune the existing method list before adding more choices.

Derivation and the three weighting alternatives are described in
[generalized-sainte-lague.md](/Users/jonasson/drive/kosningagrein/notes/generalized-sainte-lague.md).

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
visible, optional groups unchecked. A measure that belongs to multiple selected
groups should appear once. Checking a group should also avoid repeating a measure
already in the core.

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
maximum relative over- and under-representation in this optional group. The local
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
| Maximum relative under-representation (Adams) | `max_underrepresentation` |
| Total absolute deviation per reference seat | `sum_absshare`; depends on both allocation method and reference scaling |
| Total squared party-seat deviation | National party-total squared deviation; independent of local reference scaling |

Hare's absolute-deviation measure overlaps with the core. Avoid duplicate rows.
Adams' under-representation measure reaches 1 whenever a positive-reference list
receives no seats, so it often provides little discrimination in that setting.
Decision: remove “Squared values per allocated seat” entirely, including from
the optional named-method group. Its Hill–Huntington interpretation requires
positive allocations for positive-reference lists; zero-seat lists are routine
in our applications. A mathematically faithful infinite penalty would make the
measure unhelpful, and a finite replacement would lose that interpretation.

The two party-seat maxima are core measures alongside the party index; squared
party-seat deviation is optional. Present the current signed minimum as a
positive maximum shortfall.
Under- and over-allocation per reference seat and a separate squared-deviation
measure using two-way references remain undecided secondary candidates, rather
than additions to the selectable groups at this stage.

## Reference scaling and outputs

- Replace the four scaling radio buttons with independent checkboxes, allowing
  several benchmarks simultaneously. Identify them with the section headings
  above. Repeat total list seat deviation and the four list surplus/shortfall
  maxima for each selected scaling, along with enabled optional list measures.
  Keep the dedicated local indices and entropy score as single rows.
- For now, the scaling checkboxes control calculation during the simulation,
  not just display: compute and accumulate scaling-dependent measures only for
  the selected benchmarks. Showing an additional scaling after a completed run
  requires a new run. Continue computing the dedicated local indices regardless
  of scaling selection, and retain optional measures for each computed benchmark
  so their display checkboxes do not require a rerun. Scaling choices do not
  affect seat allocation or sensitivity; calculate sensitivity once, independently
  of the selected scalings. Timing may inform a later decision to compute all
  benchmarks routinely.
- Use proportions for seat-share discrepancies, not percentages or percentage
  points. Entropy score and all three Loosemore-Hanby indices use percentages.
- Optional-group selections also control CSV output. Web, CSV and Excel use one
  shared catalogue; Excel always includes the optional and secondary measures.
- Retain secondary measures in Excel, with clear names and definitions, even when
  omitted from the default web display. Pruning the display need not remove the
  underlying statistics.
- System-comparison tables are separate from this proposed core/optional-group
  redesign. Keep the current sensitivity-analysis output unchanged for now.

## Decisions to make next

1. Reconsider retaining both raw and constituency seat-share maxima after review?
2. Review the optional squared party-seat deviation after implementation?
3. Retain any other relative-deviation measures as secondary outputs?
4. Include entropy relative to system 1 in the core?


Implementation should follow these decisions, using one shared measure catalogue
for names, groups, and output selection rather than separate web and CSV lists.

## Implementation choices

- New simulations default to local scaling only. Older saved files with one
  scaling retain it; the setting now stores a list. An empty selection leaves
  the dedicated local indices, entropy (if enabled), parity and party totals.
- Both optional display selections default to unchecked. Toggling them changes
  the displayed completed results immediately; it does not change calculation.
- All six single-seat diagnostics are retained. Their reference-dependent rows
  and Excel's detailed reference matrices use the first selected benchmark in
  the order local, double, party, national (local if none is selected). The
  benchmark is identified in the diagnostic labels and report settings.
- Scaling statistics have separate identifiers for each benchmark. Seat
  allocation and sensitivity run once per replicate, not once per scaling.
- Infinite relative penalties are retained through statistics files and merging,
  displayed as infinity with unavailable SD/CI rather than finite substitutes.
- CSV uses separate section and measure fields; each average and confidence
  interval remains one cell. Excel retains secondary measures and cell comments.
