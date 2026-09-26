from division_rules import dhondt_gen, sainte_lague_gen, \
    sainte_lague_1_2_gen, sainte_lague_1_4_gen, sainte_lague_1_5_gen, \
    danish_gen, huntington_hill_gen, \
    adams_gen
from division_rules import droop, hare

from methods.common_methods import relative_superiority
from methods.common_methods import rel_sup_simple, rel_sup_medium
from methods.common_methods import max_const_vote_percentage
from methods.common_methods import max_const_seat_share
#from methods.common_methods import nearest_to_previous
from methods.common_methods import max_absolute_margin
from methods.common_methods import max_relative_margin

from methods.alternating_scaling import alt_scaling
from methods.icelandic_law import icelandic_apportionment
from methods.seats_p_unbounded import seats_p_unbounded
from methods.icelandic_law_based_on_shares import icelandic_share_apportionment
#from methods.nearest_to_previous import nearest_to_previous
#from methods.relative_superiority import relative_superiority
#from methods.relative_superiority_simple import relative_superiority_simple
#from methods.max_const_seat_share import max_const_seat_share
#from methods.max_absolute_margin import max_absolute_margin
#from methods.farthest_from_next import farthest_from_next
from methods.norwegian_law import norwegian_apportionment
from methods.switching import switching
from methods.switching_plus import switching_plus
from methods.switching_flex import switching_flex
from methods.swedish_style_switching import switching as swedish_style_switching
from methods.max_const_votes import max_const_votes
from methods.optimal_lp import optimal_lp
from methods.adjustment_as_fixed import adjustment_as_fixed
#from methods.gurobi_optimal import gurobi_optimal
from util import get_default_cpu_count


CONSTANTS = {
    'CoeffVar': 0.25,
    'ConstCorr': 0.5,
    'PartyVoteCorr': 0.5,
    'simulation_id_length': 20,
    'default_cpu_count': get_default_cpu_count()
}

DIVIDER_RULES = {
    "dhondt": dhondt_gen,
    "sainte-lague": sainte_lague_gen,
    "nordic-1.2": sainte_lague_1_2_gen,
    "nordic-1.4": sainte_lague_1_4_gen,
    "nordic-1.5": sainte_lague_1_5_gen,
    # "imperiali": imperiali_gen,
    "danish": danish_gen,
    "huntington-hill": huntington_hill_gen,
    "adams": adams_gen
}
DIVIDER_RULE_NAMES = [
    {"value": "dhondt",          "text": "D'Hondt"},
    {"value": "sainte-lague",    "text": "Sainte-Laguë"},
    {"value": "nordic-1.2",      "text": "Sainte-Laguë with 1st divisor 1.2"},
    {"value": "nordic-1.4",      "text": "Sainte-Laguë with 1st divisor 1.4"},
    {"value": "nordic-1.5",      "text": "Sainte-Laguë with 1st divisor 1.5"},
    {"value": "danish",          "text": "Danish (divisors 1, 4, 7, ...)"},
    {"value": "huntington-hill", "text": "Hill-Huntington"},
    {"value": "adams",           "text":"Adams"}
]
RULE_NAMES = [
    {"value": "dhondt",          "text": "D'Hondt"},
    {"value": "sainte-lague",    "text": "Sainte-Laguë"},
    {"value": "nordic-1.2",      "text": "Sainte-Laguë with 1st divisor 1.2"},
    {"value": "nordic-1.4",      "text": "Sainte-Laguë with 1st divisor 1.4"},
    {"value": "nordic-1.5",      "text": "Sainte-Laguë with 1st divisor 1.5"},
    {"value": "danish",          "text": "Danish"},
    {"value": "huntington-hill", "text": "Hill-Huntington"},
    {"value": "adams",           "text": "Adams"},
    {"value": "hare",            "text": "Hare quota"},
    {"value": "droop",           "text": "Droop quota"},
]

DEFAULT_ELECTION_SETTINGS = {
    "primary_divider": "dhondt",
    "constituency_threshold": 0,
    "fixed_seat_national_threshold": 0,
    "fixed_seat_threshold_choice": 1,
    "adj_determine_divider": "dhondt",
    "adjustment_threshold": 0,
    "adjustment_threshold_seats": 0,
    "adj_threshold_choice": 1,
    "require_votes_in_all_constituencies": False,
    "special_rules": "none",
    "regional_adjustment_method": "max-const-votes",
    "regional_adjustment_divider": "sainte-lague",
    "adjustment_method": "max-const-seat-share",
    "adj_alloc_divider": "dhondt",
}

ELECTION_LAW_PRESETS = [
    {
        "value": "default",
        "text": "Default",
        "settings": {
            **DEFAULT_ELECTION_SETTINGS,
            "constituency_seat_specification": "refer",
        },
    },
    {
        "value": "denmark",
        "text": "Denmark (2007–)",
        "system_name": "Denmark",
        "settings": {
            "fixed_seat_national_threshold": 0,
            "fixed_seat_threshold_choice": 0,
            "primary_divider": "dhondt",
            "constituency_threshold": 0,
            "adj_determine_divider": "hare",
            "adjustment_threshold": 2,
            "adjustment_threshold_seats": 1,
            "adj_threshold_choice": 1,
            "special_rules": "danish",
            "regional_adjustment_method": "max-const-votes",
            "regional_adjustment_divider": "sainte-lague",
            "adjustment_method": "max-const-votes",
            "adj_alloc_divider": "danish",
            "constituency_seat_specification": "refer",
        },
    },
    {
        "value": "finland",
        "text": "Finland (1907–)",
        "system_name": "Finland",
        "settings": {
            "fixed_seat_national_threshold": 0,
            "fixed_seat_threshold_choice": 0,
            "primary_divider": "dhondt",
            "constituency_threshold": 0,
            "adj_determine_divider": "dhondt",
            "adjustment_threshold": 0,
            "adjustment_threshold_seats": 0,
            "adj_threshold_choice": 1,
            "special_rules": "none",
            "adjustment_method": "adjustment-as-fixed",
            "adj_alloc_divider": "dhondt",
            "constituency_seat_specification": "refer",
        },
    },
    {
        "value": "iceland",
        "text": "Iceland (2003–)",
        "system_name": "Iceland",
        "settings": {
            "fixed_seat_national_threshold": 0,
            "fixed_seat_threshold_choice": 0,
            "primary_divider": "dhondt",
            "constituency_threshold": 0,
            "adj_determine_divider": "dhondt",
            "adjustment_threshold": 5,
            "adjustment_threshold_seats": 0,
            "adj_threshold_choice": 1,
            "special_rules": "none",
            "adjustment_method": "icelandic-law",
            "adj_alloc_divider": "dhondt",
            "constituency_seat_specification": "refer",
        },
    },
    {
        "value": "norway",
        "text": "Norway (2005–)",
        "system_name": "Norway",
        "settings": {
            "fixed_seat_national_threshold": 0,
            "fixed_seat_threshold_choice": 0,
            "primary_divider": "nordic-1.4",
            "constituency_threshold": 0,
            "adj_determine_divider": "nordic-1.4",
            "adjustment_threshold": 4,
            "adjustment_threshold_seats": 0,
            "adj_threshold_choice": 1,
            "require_votes_in_all_constituencies": True,
            "special_rules": "none",
            "adjustment_method": "norwegian-law",
            "adj_alloc_divider": "sainte-lague",
            "constituency_seat_specification": "refer",
        },
    },
    {
        "value": "sweden-2014",
        "text": "Sweden (1988–2014)",
        "settings": {
            "fixed_seat_national_threshold": 4,
            "fixed_seat_threshold_choice": 1,
            "primary_divider": "nordic-1.4",
            "constituency_threshold": 12,
            "adj_determine_divider": "nordic-1.4",
            "adjustment_threshold": 4,
            "adjustment_threshold_seats": 0,
            "adj_threshold_choice": 1,
            "special_rules": "none",
            "adjustment_method": "max-const-votes",
            "adj_alloc_divider": "sainte-lague",
            "constituency_seat_specification": "refer",
        },
    },
    {
        "value": "sweden-2018",
        "text": "Sweden (2018–)",
        "system_name": "Sweden",
        "settings": {
            "fixed_seat_national_threshold": 4,
            "fixed_seat_threshold_choice": 1,
            "primary_divider": "nordic-1.2",
            "constituency_threshold": 12,
            "adj_determine_divider": "nordic-1.2",
            "adjustment_threshold": 4,
            "adjustment_threshold_seats": 0,
            "adj_threshold_choice": 1,
            "special_rules": "swedish",
            "adjustment_method": "max-const-votes",
            "adj_alloc_divider": "sainte-lague",
            "constituency_seat_specification": "refer",
        },
    },
]

ADJUSTMENT_METHOD_NAMES = [
    {"value": "optimal-lp",                "text": "Optimal LP"},
    {"value": "alternating-scaling",       "text": "Alternating scaling"},
    {"value": "max-const-votes",           "text": "Maximum constituency votes"},
    {"value": "max-const-seat-share",      "text": "Maximum constituency seat share"},
    {"value": "max-const-vote-percentage", "text": "Maximum constituency vote percentage"},
    {"value": "switching",                 "text": "Switching of seats"},
    {"value": "switching-plus",            "text": "Switching+"},
    {"value": "switching-flex",            "text": "Flexible switching"},
    {"value": "swedish-style-switching",   "text": "Swedish-style switching"},
    {"value": "relative-sup-simple",       "text": "Relative superiority, simplified"},
    {"value": "relative-superiority",      "text": "Relative superiority"},
    {"value": "party-seats-unbounded",     "text": "Party seats unbounded"},
    {"value": "adjustment-as-fixed",       "text": "Adjustment seats as fixed seats"},
    {"value": "max-relative-margin",       "text": "Maximum relative margin (in single const.)"},
    {"value": "max-absolute-margin",       "text": "Maximum absolute margin (in single const.)"},
    {"value": "icelandic-law",             "text": "Icelandic law 112/2021"},
    {"value": "ice-shares",                "text": "Icelandic law based on constituency seat shares"},
    {"value": "norwegian-law",             "text": "Norwegian law 20/2002"},
    #{"value": "gurobi",                    "text": "Optimal with Gurobi"},    
]

SPECIAL_RULE_NAMES = [
    {"value": "none", "text": "None"},
    {"value": "danish", "text": "Danish"},
    {"value": "swedish", "text": "Swedish"},
]

REGIONAL_ADJUSTMENT_METHOD_NAMES = [
    {"value": "max-const-votes", "text": "Maximum regional votes"},
    {"value": "max-const-vote-percentage",
     "text": "Maximum regional vote percentage"},
    {"value": "max-const-seat-share", "text": "Maximum regional seat share"},
    {"value": "switching", "text": "Switching of seats"},
    {"value": "swedish-style-switching", "text": "Swedish-style switching"},
    {"value": "optimal-lp", "text": "Optimal LP"},
]

DEMO_TABLE_FORMATS = {
    "icelandic-law":             "clsl1%",
    "ice-shares":                "clsl13",
    "norwegian-law":             "clsl3",
    "max-const-seat-share":      "clsl3",
    "party-seats-unbounded":     "clsl3",
    "max-const-vote-percentage": "clsl%",
    "adjustment-as-fixed":       "clsl3",
    "relative-superiority":      "clsl3",
    "relative-sup-simple":       "clsl3",
    # "nearest-to-previous":       "clssl3",
    "max-absolute-margin":       "clcl1",
    "max-relative-margin":       "clcl3",
    "switching":                 ("sccc","clss3"),
    "switching-plus":            ("sccc", "clss3", "clsslss3"),
    "switching-flex":            ("clsl3", "clsslss3"),
    "swedish-style-switching":   ("sccc", "clss33"),
    "max-const-votes":           "clsl3",
    "alternating-scaling":       "",
    "optimal-lp":                "",
    #"gurobi":                    "",
    }
# s = special, center if all party names are less than 2 chars, else left

SEAT_SPECIFICATION_OPTIONS = {
    "const":
    [
        {"value": "refer",           "text": 'Use values from "Source votes and seats" tab'},
        {"value": "custom",          "text": "Specify numbers by changing individual values"},
        {"value": "make_const_fixed","text": "Make all constituency adjustment seats fixed"},
        {"value": "make_const_adj",  "text": "Make all constituency fixed seats adjustment seats"},
        {"value": "adams",           "text": "Distribute adjustment seats by Adams"},
        {"value": "make_all_fixed",  "text": "Make all seats fixed"},
        {"value": "make_all_adj",    "text": "Make all seats adjustment seats"},
        {"value": "one_const",       "text": "Combine all constituencies into one"},
    ],
    "party":
    [
        {"value": "totals", "text": "Constituency vote totals"},
        {"value": "party_vote_info", "text": "National party votes"},
        {"value": "average", "text": "Average of both"},
    ]
}

GENERATING_METHOD_NAMES = [
    {"value": "log-normal", "text": "Lognormal distribution"},
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
    "avg": "Average & 95% confidence interval",
    "min": "MINIMUM",
    "max": "MAXIMUM",
    "std": "STD.DEV."
}

# TODO: Add skewness and kurtosis when not parallel
# "skw": "SKEWNESS",
# "kur": "KURTOSIS"})

ADJUSTMENT_METHODS = {
    "icelandic-law":             icelandic_apportionment,
    "ice-shares":                icelandic_share_apportionment,
    "norwegian-law":             norwegian_apportionment,
    "max-const-seat-share":      max_const_seat_share,
    "party-seats-unbounded":     seats_p_unbounded,
    "adjustment-as-fixed":       adjustment_as_fixed,
    "max-const-vote-percentage": max_const_vote_percentage,
    "relative-superiority":      relative_superiority,
    "relative-sup-medium":       rel_sup_medium,
    "relative-sup-simple":       rel_sup_simple,
    # "nearest-to-previous":       nearest_to_previous,
    "max-absolute-margin":       max_absolute_margin,
    "max-relative-margin":       max_relative_margin,
    "switching":                 switching,
    "switching-plus":            switching_plus,
    "switching-flex":            switching_flex,
    "swedish-style-switching":   swedish_style_switching,
    "max-const-votes":           max_const_votes,
    "alternating-scaling":       alt_scaling,
    "optimal-lp":                optimal_lp,
    # "gurobi":                    gurobi_optimal,
    # "monge": monge,
}

REGIONAL_ADJUSTMENT_METHODS = {
    item["value"]: ADJUSTMENT_METHODS[item["value"]]
    for item in REGIONAL_ADJUSTMENT_METHOD_NAMES
}

FLEXIBLE_ADJUSTMENT_METHODS = {
    "max-const-votes", "max-const-vote-percentage",
    "swedish-style-switching", "optimal-lp", "relative-sup-simple",
    "switching-flex"}

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
    "neg_margin": "negative margin",
    "neg_margin_count": "frequency of negative margin"
}

SENS_MEASURES = [
    "sensitivity_between_parties",
    "sensitivity_within_parties",
]

PARTY_MEASURES = {
    "nat_vote_percentages": "shares of votes used for apportioning adj. seats",
    "party_ref_seat_shares": "fractional party seat totals",
    "party_total_seats": "total seats allocated to parties",
    "ref_seat_alloc": "reference seat allocation",
    "party_disparity": "disparity of allocation compared to reference",
    "party_excess": "positive disparity only or 0",
    "party_shortage": "negative disparity only (as positive number) or 0",
    "party_overhang": "potential overhang"
}

HISTOGRAM_MEASURES = {
    "disparity_count",
    "overhang_count"
}

SCALING_NAMES = {
    "both": "within both constituencies and parties",
    "const": "within constituencies",
    "party": "within parties",
    "total": "nationally",
}
