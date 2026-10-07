"""Reference benchmarks and allocation discrepancies shared by all reports."""

import numpy as np

SCALINGS = {
    "const": "Local scaling",
    "both": "Double scaling",
    "party": "Party scaling",
    "total": "National scaling",
}


def selected_scalings(value):
    """Accept old single-choice files and canonicalize the selected benchmarks."""
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)) or any(
            not isinstance(item, str) or item not in SCALINGS for item in value):
        raise ValueError("Unknown reference scaling; choose const, both, party or total.")
    return [key for key in SCALINGS if key in value]


def primary_scaling(settings):
    # Detailed matrices and historical diagnostics have a single benchmark.
    return next(iter(selected_scalings(settings.get("scaling", ["const"]))), "const")


def list_measures(seats, reference):
    seats, reference = np.asarray(seats), np.asarray(reference)
    difference = seats - reference
    positive = np.maximum(difference, 0)
    negative = np.maximum(-difference, 0)
    absolute = np.abs(difference)
    squared = difference ** 2
    # Zero-reference, zero-seat lists contribute zero. Positive allocations
    # against a zero reference have an infinite relative penalty.
    def relative(numerator):
        return np.divide(numerator, reference,
                         out=np.where(numerator > 0, np.inf, 0.),
                         where=reference > 0)
    totals = seats.sum(axis=1)[:, None]
    shares = np.divide(difference, totals, out=np.zeros_like(difference, dtype=float),
                       where=totals > 0)
    return {
        "deviation": float(absolute.sum()),
        "surplus": float(positive.max()),
        "shortfall": float(negative.max()),
        "share_surplus": float(max(0, shares.max())),
        "share_shortfall": float(max(0, -shares.min())),
        "squared": float(squared.sum()),
        "overrepresentation": float(relative(seats).max()),
        "underrepresentation": float(relative(negative).max()),
        "relative_absolute": float(relative(absolute).sum()),
        "relative_squared": float(relative(squared).sum()),
        "relative_surplus": float(relative(positive).sum()),
        "relative_shortfall": float(relative(negative).sum()),
    }


LIST_ROWS = {
    "deviation": "Total list seat deviation",
    "surplus": "Maximum seat surplus",
    "shortfall": "Maximum seat shortfall",
    "share_surplus": "Maximum seat-share surplus",
    "share_shortfall": "Maximum seat-share shortfall",
    "squared": "Total squared list seat deviation (Hare quota)",
    "overrepresentation": "Maximum relative over-representation (D'Hondt)",
    "underrepresentation": "Maximum relative under-representation (Adams)",
    "relative_absolute": "Total absolute deviation per reference seat",
}
OPTIONAL_LIST_ROWS = set(list(LIST_ROWS)[5:])
PERCENT_MEASURES = {"entropy_score", "lh_lists", "lh_constituencies", "lh_parties"}


def quality_groups(scalings, include_entropy, multiple_systems):
    """Single catalogue for computed statistics, web, CSV and Excel."""
    groups = {}
    for scaling in ["const", *[s for s in scalings if s != "const"]]:
        rows = {}
        if scaling == "const":
            rows = {
                "lh_lists": ("Loosemore-Hanby index for lists (%)", ""),
                "local_squared": ("Local squared deviation per reference seat", ""),
            }
        if scaling in scalings:
            rows.update({f"{scaling}_{key}": (title, "")
                         for key, title in LIST_ROWS.items()})
        titles = {"const": "Local measures", "both": "Measures with\ndouble scaling",
                  "party": "Measures with\nparty scaling",
                  "total": "Measures with\nnational scaling"}
        groups[scaling] = {
            "title": titles[scaling], "rows": rows, "side_title": True,
            "options": {f"{scaling}_{key}": "show_additional"
                        for key in OPTIONAL_LIST_ROWS if scaling in scalings},
        }
        if scaling == "const" and include_entropy:
            groups["entropy"] = {"title": "Quotient optimality", "side_title": True,
                                 "rows": {"entropy_score": ("Entropy score", "")}}
            if multiple_systems:
                groups["entropy"]["rows"]["entropy_relative"] = (
                    "Entropy relative to system 1", "")
    groups["parity"] = {
        "title": "Geographical balance", "side_title": True,
        "rows": {"constituency_disparity": ("Constituency disparity", ""),
                 "lh_constituencies": ("Loosemore-Hanby index for constituencies (%)", "")},
    }
    groups["toPartiesTotal"] = {
        "title": "Party totals", "side_title": True,
        "rows": {"lh_parties": ("Loosemore-Hanby index for parties (%)", ""),
                 "party_total_surplus": ("Maximum party-seat surplus", ""),
                 "party_total_shortfall": ("Maximum party-seat shortfall", ""),
                 "sum_sq_party_overall": ("Total squared party-seat deviation", "")},
        "options": {"sum_sq_party_overall": "show_additional"},
    }
    benchmark = SCALINGS[next(iter(scalings), "const")].lower()
    groups["singleSeat"] = {
        "title": "Specifically for\nsingle-seat constituencies", "side_title": True,
        "rows": {
            "bias_slope": (f"Slope of seat excess ({benchmark})", ""),
            "bias_corr": (f"Correlation of seat excess and fractional seats ({benchmark})", ""),
            "excess": ("Total party-seat excess over integer national allocation", ""),
            "max_neg_margin": (f"Maximum negative margin ({benchmark})", ""),
            "freq_neg_margin": (f"Number of constituencies with negative margin ({benchmark})", ""),
            "total_overhang": ("Potential overhang", ""),
        },
        "option": "show_single_seat",
    }
    secondary = {}
    for scaling in scalings:
        for key, title in (("relative_surplus", "Over-allocation per reference seat"),
                           ("relative_shortfall", "Under-allocation per reference seat"),
                           ("relative_squared", "Squared deviation per reference seat")):
            if key == "relative_squared" and scaling == "const":
                continue
            secondary[f"{scaling}_{key}"] = (title, SCALINGS[scaling])
    groups["secondary"] = {"title": "Secondary proportionality measures",
                           "rows": secondary, "onlyExcel": True}
    return groups


def measure_tooltip(measure):
    fixed = {
        "lh_lists": "Half the total absolute list-seat deviation, divided by total constituency seats. Uses local vote shares and each constituency's final seats, independently of the scaling selections. Lower is better.",
        "local_squared": "Sum of (allocated seats − local fractional seats) squared, divided by local fractional seats. Local fractional seats equal the local vote share times the constituency's final seats. Zero-reference lists contribute zero if they receive no seats, otherwise infinity. Lower is better.",
        "lh_constituencies": "Half the absolute deviation of constituency seat totals from their share of all constituency votes, divided by total constituency seats. Includes pruned votes. Lower is better.",
        "lh_parties": "Half the total absolute deviation of national party seats from fractional seats based on national vote shares, divided by total seats. Independent of reference scaling. Lower is better.",
        "party_total_surplus": "Largest positive difference between a party's total seats and its fractional seats based on national vote shares.",
        "party_total_shortfall": "Largest positive difference between a party's fractional seats based on national vote shares and its allocated total seats.",
        "sum_sq_party_overall": "Sum of squared differences between national party seats and fractional seats based on national vote shares.",
        "excess": "Total positive excess of party seats over the integer national reference allocation. This is not the sum of local list surpluses.",
        "max_neg_margin": "Largest value of max(0, largest list surplus − smallest list surplus − 1) within a constituency, using the first selected scaling.",
        "freq_neg_margin": "Number of constituencies with a positive negative margin, using the first selected scaling. This is a count, not a percentage.",
        "total_overhang": "Total fixed seats above parties' integer national reference allocations.",
    }
    if measure in fixed:
        return fixed[measure]
    for scaling, label in SCALINGS.items():
        prefix = scaling + "_"
        if measure.startswith(prefix):
            key = measure[len(prefix):]
            formulas = {
                "deviation": "Sum of absolute differences between allocated and fractional seats across all constituency lists (not halved).",
                "surplus": "Largest positive list difference: allocated seats minus fractional seats.",
                "shortfall": "Largest positive list difference: fractional seats minus allocated seats.",
                "share_surplus": "Largest list surplus divided by the constituency's final total seats (fixed plus adjustment). Expressed as a proportion. Constituencies with no seats are excluded.",
                "share_shortfall": "Largest list shortfall divided by the constituency's final total seats (fixed plus adjustment). Expressed as a proportion. Constituencies with no seats are excluded.",
                "squared": "Sum of squared list-seat deviations. Hare with largest remainders minimizes this in an unconstrained single constituency.",
                "overrepresentation": "Maximum allocated seats divided by fractional seats. D'Hondt minimizes this in an unconstrained single constituency.",
                "underrepresentation": "Maximum positive shortfall divided by fractional seats. Equals 1 whenever a positive-reference list receives no seats; Adams minimizes it in an unconstrained single constituency.",
                "relative_absolute": "Sum of absolute list-seat deviations divided by each list's fractional seats. A zero-seat list with positive fractional seats contributes 1.",
            }
            return f"{label}: {formulas.get(key, '')}"
    return None
