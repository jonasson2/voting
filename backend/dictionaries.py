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
from methods.switching_se import switching as switching_se
from methods.max_const_votes import max_const_votes
from methods.danish import prepare_regions
from methods.adjustment_as_fixed import adjustment_as_fixed
#from methods.gurobi_optimal import gurobi_optimal
from util import get_cpu_count


CONSTANTS = {
    'CoeffVar': 0.25,
    'ConstCorr': 0.5,
    'PartyVoteCorr': 0.5,
    'simulation_id_length': 20,
    'default_cpu_count': get_cpu_count()/2
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
    "fixed_seat_threshold_choice": 0,
    "adj_determine_divider": "dhondt",
    "adjustment_threshold": 0,
    "adjustment_threshold_seats": 0,
    "adj_threshold_choice": 1,
    "danish_special_rules": False,
    "adjustment_preparation_method": "none",
    "adj_preparation_divider": "sainte-lague",
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
            "danish_special_rules": True,
            "adjustment_preparation_method": "danish-regions",
            "adj_preparation_divider": "sainte-lague",
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
            "danish_special_rules": False,
            "adjustment_preparation_method": "none",
            "adj_preparation_divider": "sainte-lague",
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
            "danish_special_rules": False,
            "adjustment_preparation_method": "none",
            "adj_preparation_divider": "sainte-lague",
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
            "danish_special_rules": False,
            "adjustment_preparation_method": "none",
            "adj_preparation_divider": "sainte-lague",
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
            "danish_special_rules": False,
            "adjustment_preparation_method": "none",
            "adj_preparation_divider": "nordic-1.4",
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
            "danish_special_rules": False,
            "adjustment_preparation_method": "switching_se",
            "adj_preparation_divider": "nordic-1.2",
            "adjustment_method": "max-const-votes",
            "adj_alloc_divider": "sainte-lague",
            "constituency_seat_specification": "refer",
        },
    },
]

ADJUSTMENT_METHOD_NAMES = [
    {"value": "icelandic-law", "text": "Icelandic law 112/2021"},
    {"value": "ice-shares",    "text": "Icelandic law based on constituency seat shares"},
    {"value": "norwegian-law", "text": "Norwegian law 20/2002"},
    {"value": "max-const-seat-share",      "text": "Maximum constituency seat share"},
    {"value": "party-seats-unbounded",     "text": "Party seats unbounded"},
    {"value": "max-const-vote-percentage", "text": "Maximum constituency vote percentage"},
    {"value": "adjustment-as-fixed",       "text": "Adjustment seats as fixed seats"},
    {"value": "relative-superiority",      "text": "Relative superiority"},
    {"value": "relative-sup-simple",       "text": "Relative superiority, simplified"},
    # {"value": "nearest-to-previous",       "text": "Nearest-to-previous"},
    {"value": "max-relative-margin",       "text": "Maximum relative margin"},
    {"value": "max-absolute-margin",       "text": "Maximum absolute margin"},
    # = max-relative-margin með absolute mun
    {"value": "switching",                 "text": "Switching of seats"},
    {"value": "max-const-votes",           "text": "Maximum constituency votes"},
    {"value": "alternating-scaling",       "text": "Optimal divisor method"},
    #{"value": "gurobi",                    "text": "Optimal with Gurobi"},    
]

ADJUSTMENT_PREPARATION_METHOD_NAMES = [
    {"value": "none", "text": "None"},
    {"value": "switching_se", "text": "Swedish switching"},
    {"value": "danish-regions", "text": "Danish allocation to regions"},
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
    "max-const-votes":           "clsl3",
    "alternating-scaling":       "",
    #"gurobi":                    "",
    }
# s = special, center if all party names are less than 2 chars, else left

SEAT_SPECIFICATION_OPTIONS = {
    "const":
    [
        {"value": "refer",           "text": 'Use values from "Source votes and seats" tab'},
        {"value": "custom",          "text": "Specify numbers by changing individual values"},
        {"value": "make_const_fixed","text": "Make all constituency seats fixed"},
        {"value": "make_const_adj",  "text": "Make all constituency seats adjustment seats"},
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

ADJUSTMENT_PREPARATION_METHODS = {
    "switching_se": switching_se,
    "danish-regions": prepare_regions,
}

ADJUSTMENT_PREPARATION_DEMO_TABLE_FORMATS = {
    "switching_se": "clss33",
    "danish-regions": "clscc3l",
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
    "avg": "AVG 95%-CI",
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
    "max-const-votes":           max_const_votes,
    "alternating-scaling":       alt_scaling,
    # "gurobi":                    gurobi_optimal,
    # "monge": monge,
}

FLEXIBLE_ADJUSTMENT_METHODS = {"max-const-votes"}

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
    "party_sens",
    "list_sens"
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
