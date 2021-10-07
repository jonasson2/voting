
from division_rules import dhondt_gen, sainte_lague_gen, \
    nordic_sainte_lague_gen, imperiali_gen, danish_gen, huntington_hill_gen
from division_rules import droop, hare

from methods.var_alt_scal import var_alt_scal
from methods.alternating_scaling import alternating_scaling
from methods.icelandic_law import icelandic_apportionment
from methods.icelandic_law_based_on_shares import icelandic_share_apportionment
from methods.monge import monge
from methods.nearest_neighbor import nearest_neighbor
from methods.relative_superiority import relative_superiority
from methods.relative_superiority_simple import relative_superiority_simple
from methods.norwegian_law import norwegian_apportionment
from methods.norwegian_icelandic import norw_ice_apportionment
from methods.pure_vote_ratios import pure_vote_ratios_apportionment
from methods.opt_entropy import opt_entropy
from methods.switching import switching

from distributions.beta_distribution import beta_distribution
from distributions.uniform_distribution import uniform_distribution

DIVIDER_RULES = {
    "1-dhondt": dhondt_gen,
    "2-sainte-lague": sainte_lague_gen,
    "3-nordic": nordic_sainte_lague_gen,
    # "imperiali": imperiali_gen,
    "4-danish": danish_gen,
    "5-huntington-hill": huntington_hill_gen,
}
DIVIDER_RULE_NAMES = {
    "1-dhondt": "D'Hondt",
    "2-sainte-lague": "Sainte-Laguë",
    "3-nordic": "Nordic Sainte-Laguë variant",
    "4-danish": "Danish",
    "5-huntington-hill": "Huntington-Hill",
}
QUOTA_RULES = {
    "6-hare": hare,
    "7-droop": droop,
}
RULE_NAMES = {
    "1-dhondt":          "D'Hondt",
    "2-sainte-lague":    "Sainte-Laguë",
    "3-nordic":          "Nordic Sainte-Laguë variant",
    "4-danish":          "Danish",
    "5-huntington-hill": "Huntington-Hill",
    "6-hare":            "Hare quota",
    "7-droop":           "Droop quota",
    #"imperiali": "Imperiali method",
}

ADJUSTMENT_METHODS = {
    # "var-alt-scal": var_alt_scal,
    "1-icelandic-law": icelandic_apportionment,
    "2-ice-shares": icelandic_share_apportionment,
    "3-norwegian-law": norwegian_apportionment,
    "4-norwegian-icelandic": norw_ice_apportionment,
    "5-pure-vote-ratios": pure_vote_ratios_apportionment,
    "6-relative-superiority": relative_superiority,
    "7-relative-sup-simple": relative_superiority_simple,
    "8-nearest-neighbor": nearest_neighbor,
    "9-monge": monge,
    # "opt-entropy": opt_entropy,
    "A-switching": switching,
    "B-alternating-scaling": alternating_scaling,
}
ADJUSTMENT_METHOD_NAMES = {
    "1-icelandic-law":        "Icelandic law 24/2000",
    "2-ice-shares":           "Icelandic law based on seat shares",
    "3-norwegian-law":        "Norwegian law 20/2002",
    "4-norwegian-icelandic":  "Norwegian law based on seat shares",
    "5-pure-vote-ratios":     "Vote percentage",
    "6-relative-superiority": "Relative superiority",
    "7-relative-sup-simple":  "Relative superiority, simplified",
    "8-nearest-neighbor":     "Nearest neighbor",
    "9-monge":                "Monge",
    "A-switching":            "Switching of seats",
    "B-alternating-scaling":  "Optimal divisor method",
}

GENERATING_METHODS = {
    "beta": beta_distribution,
    "uniform": uniform_distribution,
    "maxchange": None
}

GENERATING_METHOD_NAMES = {
    "beta": "Beta distribution",
    "uniform": "Uniform distribution",
    "maxchange": "Maximum change method"
}

SEAT_SPECIFICATION_OPTIONS = {
    "refer":          'Use values from "Votes and seats" tab',
    "custom":         "Specify seat numbers by changing individual values",
    "make_all_const": "Make all seats constituency seats",
    "make_all_adj":   "Make all seats adjustment seats",
    "one_const":      "Combine all constituencies into one",
}

MEASURES = {
    "dev_opt":         "Allocation by the optimal method",
    "dev_opt_totals":  "Allocation by the optimal method",
    "dev_law":         "Allocation by Icelandic law",
    "dev_law_totals":  "Allocation by Icelandic law",
    "dev_all_adj":     "Allocation as if all seats were adjustment seats",
    "dev_all_adj_totals":
                       "Allocation as if all seats were adjustment seats",
    "dev_all_const":   "Allocation as if all seats were constituency seats",
    "dev_all_const_totals":
                       "Allocation as if all seats were constituency seats",
    "dev_ref":         "Allocation based on reference votes",
    "dev_ref_totals":  "Allocation based on reference votes",
    "adj_dev":         "Desired apportionment of adjustment seats",
    "dev_one_const":   "Allocation as if all constituencies were combined into one",
    "entropy":         "Entropy (product of all seat values used)",
    "entropy_ratio":   "Entropy relative to optimal value",
    "min_seat_value":  "Mininum seat value used (based on selected reference seat shares)",
    "sum_abs":         "Sum of absolute differences",
    "sum_pos":         "Sum of relative positive differences",
    "sum_sq":          "Sum of relative squared differences",
}
LIST_DEVIATION_MEASURES = [
    "dev_opt",
    "dev_law",
    "dev_all_adj",
    "dev_all_const",
    "dev_ref",
    # "dev_one_const", #skipped, because already measured by all_adj (party sums)
]
TOTALS_DEVIATION_MEASURES = [
    #"dev_opt_totals",
    #"dev_law_totals",
    "dev_all_adj_totals",
    "dev_all_const_totals",
    "dev_ref_totals",
    "adj_dev",
]
STANDARDIZED_MEASURES = [
    "entropy_ratio",
    "min_seat_value",
]
IDEAL_COMPARISON_MEASURES = [
    "sum_abs",
    "sum_pos",
    "sum_sq",
]
LIST_MEASURES = {
    "const_seats":   "constituency seats",
    "adj_seats":     "adjustment seats",
    "total_seats":   "constituency and adjustment seats combined",
    "seat_shares":   "total seats normalized within each constituency",
    "ideal_seats":   "ideal seat shares",
    # "dev_opt":       "deviation from optimal solution",
    # "dev_law":       "deviation from official law method",
    # "dev_all_const": "deviation from Independent Constituencies",
    # "dev_one_const": "deviation from Single Constituency",
    # "dev_all_adj":   "deviation from All Adjustment Seats"
}
VOTE_MEASURES = {
    "sim_votes":  "votes in simulations",
    "sim_shares": "shares in simulations",
}
AGGREGATES = {
    "cnt": "Number of elements",
    "max": "Max",
    "min": "Min",
    "sum": "Sum of elements",
    "sm2": "Sum of squares",
    "sm3": "Sum of cubes",
    "sm4": "Sum of fourth powers",
    "avg": "Average",
    "var": "Variance",
    "std": "Std. dev",
    "skw": "Skewness",
    "kur": "Kurtosis",
}
