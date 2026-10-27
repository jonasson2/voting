# TODO

## Quality measures and allocation methods

1. [x] Include Total list seat deviation in Additional proportionality measures
   for all reference scalings.
2. [x] Review the method names in parentheses after quality-measure names.
   Þorkell questions “Total squared list seat deviation (Hare quota)”: check
   exactly what Hare minimizes and under which assumptions. Review all such
   associations, including Hare, Sainte-Laguë, D'Hondt and Adams. Distinguish
   single-constituency apportionment from allocation across constituency lists
   with prescribed party totals and protected fixed seats. Correct or remove
   misleading labels and explanations; check zero-seat and zero-reference cases.
3. [x] Review under-allocation and under-representation measures. Remove Maximum
   relative under-representation from all reports. Retain the Excel-only sum
   as Total relative seat shortfall, with a comment explaining that each
   unrepresented positive-reference list contributes 1 regardless of its size.
4. [x] Review switching with minimum and maximum adjustment-seat counts: fix
   reported errors and determine how to adapt it to constituencies of unequal
   size. Review relative-superiority methods (rel-sup) on the same points.
   - Probably fixed.
5. [x] Add exact generalized Sainte-Laguë and its switching approximation.
   Follow the existing [method and weighting note](../kosningagrein/notes/generalized-sainte-lague.md)
   and the agreed seat weighting in [measures.md](measures.md#local-sainte-laguë-measure-and-candidate-methods).
   Implemented as Seat-share optimization (LP) and Seat-share switching, with
   fixed constituency totals and a selectable divisor rule. Sainte-Laguë
   minimizes the agreed squared-deviation measure; D'Hondt and other divisor
   rules use their corresponding cumulative marginal costs. Names are provisional.

## Norwegian method names

6. [x] Investigate how to rename the methods currently called Maximum
   constituency seat share and Norwegian law, including their relationship to
   the Norway election-law preset. Verify the proposed distinction and decide
   how to present it consistently. Earlier discussion, retained as a hint:

   > Yes. They describe the distinction more clearly: both methods rank a
   > party’s next-seat quotient, weighted by the constituency’s seat count. The
   > Norwegian method uses fixed seats; the other uses total seats. Norway’s
   > official report calls its score a vektet mandatkvotient.

   > For a matched pair of simulator labels, I’d choose “Fixed-seat weighted
   > quotient (Norwegian)” and “Total-seat weighted quotient.” “Norwegian
   > weighted quotient” is also reasonable, but the matched pair makes the
   > difference visible without opening the settings.

   Implemented these matched names in method selectors and allocation tables.
   The displayed fixed-seat method name omits “(Norwegian)”; its tooltip says
   “Fixed-seat weighted quotient (Norwegian law)”.
   The Norway election-law preset keeps its name. Retain `max(1, fixed seats)`
   without a special interface qualification; saved method identifiers stay unchanged.

## Tutorial, language and explanations

7. [ ] Update and complete the [short tutorial](doc/leidbeiningar-stuttar.md)
   and translate it into English. Update the interface descriptions, measure
   names, output blocks and confidence
   intervals. Remove references to the deleted Difference column and comparison
   selector, and rerun examples before publishing their numerical results.
8. [ ] Expand the tutorial with a third worked example and a section on other
   features. Reconcile the Norway outline near the end of the short tutorial
   with the [provisional Sweden chapter](doc/leidbeiningar-naesti-kafli.md).
   Cover Upload/Download for individual sections and all settings, both Excel
   downloads, Settings, national party votes, reference scaling, simulation
   distributions/correlation/CPU count, thresholds, sensitivity, flexible
   adjustment seats and alternative seat specifications.
9. [ ] Translate the simulator interface to Icelandic once the interface and
   terminology have stabilized. Recovered from the previous TODO list.
10. [ ] Add translations into other languages.
11. [ ] Write a separate mathematical description of the allocation methods and
    quality measures, with a glossary. Keep the tutorial practical and refer to
    this document for mathematical details.
12. [ ] **Glossary.** Clarify terminology and explain the allocation methods and measures:
    fractional reference seats, the scaling choices, reference systems and
    comparison systems. Terminology clarification was also recorded in the
    previous TODO list.

## Excel

13. [ ] Review the explanatory cell comments in Excel reports, including
    Excel-only measures. Check that they contain complete, correct definitions,
    formulas, units, reference scalings and relevant zero-seat/zero-reference
    conventions. Add missing explanations; some secondary measures currently
    have only the scaling name as their comment.

14. [ ] Review the Excel-only measures and how they are split into display
    sections. Check which measures to retain and organize them into clear,
    appropriate blocks and subblocks.

## Interface and settings

15. [ ] Review the Electoral systems tab's tooltips, including those for the
    adjustment-seat method dropdown list.
16. [x] Add selectable terminology in the Settings tab.
    - [x] Constituencies: constituency, district, or electorate; reusable helpers,
      browser preference, and Excel/CSV report labels.
    - [x] Adjustment seats: adjustment, compensatory, equalization, levelling,
      or top-up; browser preference and Excel/CSV report labels.
17. [x] Redesign the selection of the adjustment-seat allocation method.
    Select a family, then a method, then RSSS scaling or the divisor rule
    where applicable. Families: Country laws, Optimal methods,
    Approximations to optimal methods, Single-seat constituency methods, and
    Other exploratory methods. Basic Switching, Swedish-style switching
    and alternating scaling are exploratory. The approximation family contains
    Entropy switching (formerly Flexible switching), Seat-share switching,
    RSSS MinL1 switching and RSSS MinL2 switching. Switching+ is removed.
    Saved-system formats are unchanged; Entropy switching keeps the existing
    `switching-flex` identifier.
    - [x] Add RSSS switching approximations with the corresponding objective
      functions and both reference scalings, using the shared exchange engine.

The former “Decisions to make next” list in measures.md is complete and is not
an outstanding task list. The recovered geographical-measure notes describe
implemented work, not pending tasks.
