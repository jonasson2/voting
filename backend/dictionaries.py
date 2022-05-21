from division_rules import dhondt_gen, sainte_lague_gen, \
    nordic_sainte_lague_gen, imperiali_gen, danish_gen, huntington_hill_gen
from division_rules import droop, hare

from methods.alternating_scaling import alt_scaling
from methods.icelandic_law import icelandic_apportionment
from methods.icelandic_law_based_on_shares import icelandic_share_apportionment
# from methods.monge import monge
from methods.nearest_to_previous import nearest_to_previous
from methods.relative_superiority import relative_superiority
from methods.relative_superiority_simple import relative_superiority_simple
from methods.norwegian_law import norwegian_apportionment
from methods.max_const_seat_share import norw_ice_apportionment
from methods.max_const_vote_percentage import max_const_vote_percentage_apportionment
from methods.opt_entropy import opt_entropy
from methods.switching import switching
from util import get_cpu_count
from methods.farthest_from_next import farthest_from_next

from distributions.symmetric_beta_distribution import symmetric_beta_distribution
from distributions.gamma_distribution import gamma_distribution
from distributions.uniform_distribution import uniform_distribution

CONSTANTS = {
    'minimum_votes': 1e-6,
    'CoeffVar': 0.25,
    'simulation_id_length': 20,
    'default_cpu_count': get_cpu_count()/2
}

DIVIDER_RULES = {
    "dhondt": dhondt_gen,
    "sainte-lague": sainte_lague_gen,
    "nordic": nordic_sainte_lague_gen,
    # "imperiali": imperiali_gen,
    "danish": danish_gen,
    "huntington-hill": huntington_hill_gen,
}
DIVIDER_RULE_NAMES = [
    {"value": "dhondt",          "text": "D'Hondt"},
    {"value": "sainte-lague",    "text": "Sainte-Laguë"},
    {"value": "nordic",          "text": "Nordic Sainte-Laguë variant"},
    {"value": "danish",          "text": "Danish"},
    {"value": "huntington-hill", "text": "Hill-Huntington"},
]
RULE_NAMES = [
    {"value": "dhondt",          "text": "D'Hondt"},
    {"value": "sainte-lague",    "text": "Sainte-Laguë"},
    {"value": "nordic",          "text": "Nordic Sainte-Laguë variant"},
    {"value": "danish",          "text": "Danish"},
    {"value": "huntington-hill", "text": "Hill-Huntington"},
    {"value": "hare",            "text": "Hare quota"},
    {"value": "droop",           "text": "Droop quota"},
]
ADJUSTMENT_METHOD_NAMES = [
    {"value": "icelandic-law", "text": "Icelandic law 112/2021"},
    {"value": "ice-shares",    "text": "Icelandic law based on constituency seat shares"},
    {"value": "norwegian-law", "text": "Norwegian law 20/2002"},
    {"value": "max-const-seat-share",      "text": "Maximum constituency seat share"},
    {"value": "max-const-vote-percentage", "text": "Maximum constituency vote percentage"},
    {"value": "relative-superiority",      "text": "Relative superiority"},
    {"value": "relative-sup-simple",       "text": "Relative superiority, simplified"},
    {"value": "nearest-to-previous",       "text": "Nearest-to-previous"},
    {"value": "farthest-from-next",        "text": "Farthest-from-next"},
    # "monge", "text":                "Monge"},
    {"value": "switching",                 "text": "Switching of seats"},
    {"value": "alternating-scaling",       "text": "Optimal divisor method"},
]
DEMO_TABLE_FORMATS = {
    "icelandic-law":             "clsl1%",
    "ice-shares":                "clsl13",
    "norwegian-law":             "clsl3",
    "max-const-seat-share":      "clsl3",
    "max-const-vote-percentage": "clsl%",
    "relative-superiority":      "clsl3",
    "relative-sup-simple":       "clsl3",
    "nearest-to-previous":       "clssl3",
    "farthest-from-next":        "clssl3",
    "switching":                 ("sccc","clss3"),
    "alternating-scaling":       ""}
# s = special, center if all party names are less than 2 chars, else left

SEAT_SPECIFICATION_OPTIONS = [
    {"value": "refer",          "text": 'Use values from "Source votes and seats" tab'},
    {"value": "custom",         "text": "Specify seat numbers by changing individual values"},
    {"value": "make_all_const", "text": "Make all seats constituency seats"},
    {"value": "make_all_adj",   "text": "Make all seats adjustment seats"},
    {"value": "one_const",      "text": "Combine all constituencies into one"},
]

GENERATING_METHOD_NAMES = [
    {"value": "gamma",   "text": "Gamma distribution"},
    {"value": "beta",    "text": "Symmetric beta distribution"},
    {"value": "uniform", "text": "Uniform distribution"},
]

QUOTA_RULES = {
    "hare": hare,
    "droop": droop,
}

EXCEL_HEADINGS = {
    "avg":  "AVERAGE",
    "lo95": "LOWER 95%-CI",
    "hi95": "UPPER 95%-CI",
    "min":  "MINIMUM",
    "max":  "MAXIMUM",
    "std":  "STD.DEV."
}    

STATISTICS_HEADINGS = {
    "avg": "AVG 95%-CI",
    "min": "MINIMUM",
    "max": "MAXIMUM",
    "std": "STD.DEV."
}

# TODO: Add skewness and kurtosis when not parallel
# "skw": "SKEWNESS",
# "kur": "KURTOSIS"})

ADJUSTMENT_METHODS = {
    "icelandic-law": icelandic_apportionment,
    "ice-shares": icelandic_share_apportionment,
    "norwegian-law": norwegian_apportionment,
    "max-const-seat-share": norw_ice_apportionment,
    "max-const-vote-percentage": max_const_vote_percentage_apportionment,
    "relative-superiority": relative_superiority,
    "relative-sup-simple": relative_superiority_simple,
    "nearest-to-previous": nearest_to_previous,
    "farthest-from-next": farthest_from_next,
    # "monge": monge,
    # "opt-entropy": opt_entropy,
    "switching": switching,
    "alternating-scaling": alt_scaling,
}

GENERATING_METHODS = {
    "gamma": gamma_distribution,
    "beta": symmetric_beta_distribution,
    "uniform": uniform_distribution
}

# MEASURES = {
#     "dev_all_adj":  "Allocation as if all seats were adjustment seats",
#     "dev_all_adj_tot":
#                     "Allocation as if all seats were adjustment seats",
#     "dev_all_const":"Allocation as if all seats were constituency seats",
#     "dev_all_const_tot":
#                     "Allocation as if all seats were constituency seats",
#     "dev_ref":      "Allocation with actual system for the reference votes",
#     "dev_ref_tot":  "Allocation with actual system for the reference votes",
#     #"adj_dev":      "Desired apportionment of adjustment seats",
#     "one_const_tot":"Allocation as if all constituencies were combined into one",
#     "entropy":      "Entropy (logarithmic)",
#     "min_seat_val": "Mininum reference seat share per seat",
#     "sum_abs":      "Sum of absolute values",
#     "sum_pos":       "Sum of positive values",
#     "sum_sq":        "Sum of squared values",
# }
# LIST_DEVIATION_MEASURES = [
#     "dev_all_adj",
#     "dev_all_const",
#     "dev_ref",
# ]
# TOTALS_DEVIATION_MEASURES = [
#     #"dev_opt_totals",
#     #"dev_law_totals",
#     "dev_all_adj_tot",
#     "dev_all_const_tot",
#     "dev_ref_tot",
# ]
# STANDARDIZED_MEASURES = [
#     "entropy",
#     "min_seat_val",
# ]
# IDEAL_COMPARISON_MEASURES = [
#     "sum_abs",
#     "sum_pos",
#     "sum_sq",
# ]
LIST_MEASURES = {
    "const_seats":   "constituency seats",
    "adj_seats":     "adjustment seats",
    "total_seats":   "constituency and adjustment seats combined",
    "seat_shares":   "total seats normalized within each constituency",
    "ideal_seats":   "ideal seat shares",
}
VOTE_MEASURES = {
    "sim_votes":  "votes in simulations",
    "sim_shares": "shares in simulations",
}

SENS_MEASURES = [
    "party_sens",
    "list_sens"
]

SCALING_NAMES = {
    "both": "within both constituencies and parties",
    "const": "within constituencies",
    "party": "within parties",
    "total": "nationally",
}
