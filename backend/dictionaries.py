from division_rules import dhondt_gen, sainte_lague_gen, \
    nordic_sainte_lague_gen, danish_gen, huntington_hill_gen, \
    adams_gen
from division_rules import droop, hare

from methods.alternating_scaling import alt_scaling
from methods.icelandic_law import icelandic_apportionment
from methods.icelandic_law_based_on_shares import icelandic_share_apportionment
# from methods.monge import monge
from methods.nearest_to_previous import nearest_to_previous
from methods.relative_superiority import relative_superiority
from methods.relative_superiority_simple import relative_superiority_simple
from methods.norwegian_law import norwegian_apportionment
from methods.max_const_seat_share import const_seat_share_apportionment
from methods.max_const_vote_percentage import max_const_vote_percentage_apportionment
from methods.opt_entropy import opt_entropy
from methods.switching import switching
from util import get_cpu_count
from methods.farthest_from_next import farthest_from_next

from distributions.symmetric_beta_distribution import symmetric_beta_distribution
from distributions.gamma_distribution import gamma_distribution
from distributions.uniform_distribution import uniform_distribution

CONSTANTS = {
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
    "adams": adams_gen
}
DIVIDER_RULE_NAMES = [
    {"value": "dhondt",          "text": "D'Hondt"},
    {"value": "sainte-lague",    "text": "Sainte-Laguë"},
    {"value": "nordic",          "text": "Nordic Sainte-Laguë variant"},
    {"value": "danish",          "text": "Danish"},
    {"value": "huntington-hill", "text": "Hill-Huntington"},
    {"value": "adams",           "text":"Adams"}
]
RULE_NAMES = [
    {"value": "dhondt",          "text": "D'Hondt"},
    {"value": "sainte-lague",    "text": "Sainte-Laguë"},
    {"value": "nordic",          "text": "Nordic Sainte-Laguë variant"},
    {"value": "danish",          "text": "Danish"},
    {"value": "huntington-hill", "text": "Hill-Huntington"},
    {"value": "adams",          "text": "Adams"},
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

SEAT_SPECIFICATION_OPTIONS = {
    "const":
    [
        {"value": "refer",          "text": 'Use values from "Source votes and seats" tab'},
        {"value": "custom",         "text": "Specify numbers by changing individual values"},
        {"value": "make_all_fixed", "text": "Make all seats fixed seats"},
        {"value": "make_all_adj",   "text": "Make all seats adjustment seats"},
        {"value": "one_const",      "text": "Combine all constituencies into one"},
    ],
    "party":
    [
        {"value": "totals",      "text": ('Base on constituency vote totals in '
                                          '"Source votes and seats" tab')},
        {"value": "party_vote_info", "text": ('Base on national party votes in '
                                          '"Source votes and seats" tab')},
        {"value": "average",     "text": ('Base on average of constituency vote '
                                          'totals and national party votes')},
    ]
}

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
    "max-const-seat-share": const_seat_share_apportionment,
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

USE_THRESHOLDS = [
    {"value": False, "text": "no"},
    {"value": True, "text": "yes"}    
]

THRESHOLD_CHOICE = [
    {"value": 0,          "text": "and"},
    {"value": 1,          "text": "or"}
]

SEAT_MEASURES = {
    "ref_seat_shares": "reference seat shares",
    "fixed_seats": "fixed seats",
    "adj_seats": "adjustment seats",
    "total_seats": "constituency and adjustment seats combined",
    "total_seat_percentages": "total seats normalized within each constituency",
}
VOTE_MEASURES = {
    "sim_votes": "votes in simulations",
    "sim_vote_percentages": "shares in simulations",
}

SENS_MEASURES = [
    "party_sens",
    "list_sens"
]

PARTY_VOTE_MEASURES = [
    ""
]

SCALING_NAMES = {
    "both": "within both constituencies and parties",
    "const": "within constituencies",
    "party": "within parties",
    "total": "nationally",
}
