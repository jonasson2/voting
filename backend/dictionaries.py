from division_rules import dhondt_gen, sainte_lague_gen, \
    nordic_sainte_lague_gen, imperiali_gen, danish_gen, huntington_hill_gen
from division_rules import droop, hare

from methods.alternating_scaling import alt_scaling
from methods.icelandic_law import icelandic_apportionment
from methods.icelandic_law_based_on_shares import icelandic_share_apportionment
# from methods.monge import monge
from methods.nearest_neighbor import nearest_neighbor
from methods.relative_superiority import relative_superiority
from methods.relative_superiority_simple import relative_superiority_simple
from methods.norwegian_law import norwegian_apportionment
from methods.norwegian_icelandic import norw_ice_apportionment
from methods.pure_vote_ratios import pure_vote_ratios_apportionment
from methods.opt_entropy import opt_entropy
from methods.switching import switching

from distributions.symmetric_beta_distribution import symmetric_beta_distribution
from distributions.gamma_distribution import gamma_distribution
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
    "1-icelandic-law": icelandic_apportionment,
    "2-ice-shares": icelandic_share_apportionment,
    "3-norwegian-law": norwegian_apportionment,
    "4-norwegian-icelandic": norw_ice_apportionment,
    "5-pure-vote-ratios": pure_vote_ratios_apportionment,
    "6-relative-superiority": relative_superiority,
    "7-relative-sup-simple": relative_superiority_simple,
    "8-nearest-neighbor": nearest_neighbor,
    # "9-monge": monge,
    # "opt-entropy": opt_entropy,
    "A-switching": switching,
    "B-alternating-scaling": alt_scaling,
}
ADJUSTMENT_METHOD_NAMES = {
    "1-icelandic-law":        "Icelandic law 24/2000",
    "2-ice-shares":           "Icelandic law based on constituency seat shares",
    "3-norwegian-law":        "Norwegian law 20/2002",
    "4-norwegian-icelandic":  "Maximum constituency seat share",
    "5-pure-vote-ratios":     "Maximum constituency vote percentage",
    "6-relative-superiority": "Relative superiority",
    "7-relative-sup-simple":  "Relative superiority, simplified",
    "8-nearest-neighbor":     "Nearest neighbor",
    # "9-monge":                "Monge",
    "A-switching":            "Switching of seats",
    "B-alternating-scaling":  "Optimal divisor method",
}

GENERATING_METHODS = {
    "beta": symmetric_beta_distribution,
    "gamma": gamma_distribution,
    "uniform": uniform_distribution,
    "maxchange": None
}

GENERATING_METHOD_NAMES = [
    {"value": "gamma",     "text": "Gamma distribution"},
    {"value": "beta",      "text": "Symmetric beta distribution"},
    {"value": "uniform",   "text": "Uniform distribution"},
    {"value": "maxchange", "text": "Maximum change method"}
]

SEAT_SPECIFICATION_OPTIONS = {
    "refer":          'Use values from "Source votes and seats" tab',
    "custom":         "Specify seat numbers by changing individual values",
    "make_all_const": "Make all seats constituency seats",
    "make_all_adj":   "Make all seats adjustment seats",
    "one_const":      "Combine all constituencies into one",
}

MEASURES = {
    "dev_all_adj":  "Allocation as if all seats were adjustment seats",
    "dev_all_adj_tot":
                    "Allocation as if all seats were adjustment seats",
    "dev_all_const":"Allocation as if all seats were constituency seats",
    "dev_all_const_tot":
                    "Allocation as if all seats were constituency seats",
    "dev_ref":      "Allocation with actual system for the reference votes",
    "dev_ref_tot":  "Allocation with actual system for the reference votes",
    #"adj_dev":      "Desired apportionment of adjustment seats",
    "one_const_tot":"Allocation as if all constituencies were combined into one",
    "entropy":      "Entropy (product of all seat values used)",
    "min_seat_val": "Mininum allocation seat share used",
    "sum_abs":      "Sum of absolute differences of shares minus seats",
    "sum_pos":       "Positive differences relative to the shares",
    "sum_sq":        "Squared differences relative to the shares",
}
LIST_DEVIATION_MEASURES = [
    "dev_all_adj",
    "dev_all_const",
    "dev_ref",
]
TOTALS_DEVIATION_MEASURES = [
    #"dev_opt_totals",
    #"dev_law_totals",
    "dev_all_adj_tot",
    "dev_all_const_tot",
    "dev_ref_tot",
]
STANDARDIZED_MEASURES = [
    "entropy",
    "min_seat_val",
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
    "avg": "Average",
    "std": "Std. dev",
    "max": "Max",
    "min": "Min",
    "skw": "Skewness",
    "kur": "Kurtosis",
}

STAT_LIST = AGGREGATES.keys()
