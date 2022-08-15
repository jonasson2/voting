import json
from copy import copy, deepcopy
#from system import System
#from util import load_constituencies
from util import disp, remove_prefix
from dictionaries import DIVIDER_RULES, QUOTA_RULES, ADJUSTMENT_METHODS
class ElectionSystem(dict):
    """A set of rules for an election to follow."""

    def __init__(self):
        self["name"] = "System"

        # Election systems
        self["primary_divider"] = "dhondt"
        self["adj_determine_divider"] = "dhondt"
        self["adj_alloc_divider"] = "dhondt"
        self["adjustment_threshold"] = 0
        self["adjustment_threshold_seats"] = 0
        self["adj_threshold_choice"] = 0
        self["constituency_threshold"] = 0
        self["adjustment_method"] = "icelandic-law"
        self["seat_spec_options"] = {"const": "refer", "party": "totals"}
        self["compare_with"] = False
        self["parties"] = []

    def __deepcopy__(self, memo):
        ES = ElectionSystem()
        ES.update({k:deepcopy(v,memo) for (k,v) in self.items()})
        return ES

    def get_generator(self, div):
        """Fetch a generator from divider systems."""
        method = self[div]
        if method in DIVIDER_RULES.keys():
            return DIVIDER_RULES[method]
        elif method in QUOTA_RULES.keys():
            return QUOTA_RULES[method]
        else:
            raise ValueError("%s is not a known divider" % div)

    def get_type(self, rule):
        method = self[rule]
        if method in DIVIDER_RULES.keys():
            return "Division"
        elif method in QUOTA_RULES.keys():
            return "Quota"
        else:
            raise ValueError(f"{rule} is not a known rule")

    def generate_system(self, option, vote_table = []):
        option = remove_prefix(option, "make_")
        sys = copy(self)
        if option in {"all_fixed","const_fixed"}:
            sys["constituencies"] = set_const_fixed(self["constituencies"])
        elif option in {"all_adj", "const_adj"}:
            sys["constituencies"] = set_const_adj(self["constituencies"])
        elif option == "one_const":
            sys["constituencies"] = set_one_const(self["constituencies"])
        else:
            raise ValueError
        return sys

def copyconst(const):
    constlist = [copy(c) for c in const]
    return constlist

def set_one_const(constituencies):
    one_const = [{
        "name": "All",
        "num_fixed_seats": sum(
            [const["num_fixed_seats"] for const in constituencies]),
        "num_adj_seats": sum(
            [const["num_adj_seats"] for const in constituencies]),
    }]
    return one_const

def set_nat_seats(pvi):
    nat_seats = {"num_fixed_seats": pvi['num_fixed_seats'],
                 "num_adj_seats": pvi['num_adj_seats']}
    return nat_seats

def set_nat_seats_fixed(pvi):
    nat_seats = {}
    nat_seats["num_fixed_seats"] = pvi['num_fixed_seats'] + pvi['num_adj_seats']
    nat_seats["num_adj_seats"] = 0
    return nat_seats

def set_nat_seats_adj(pvi):
    nat_seats = {}
    nat_seats["num_adj_seats"] = pvi['num_fixed_seats'] + pvi['num_adj_seats']
    nat_seats["num_fixed_seats"] = 0
    return nat_seats

def set_const_adj(constituencies):
    all_adj = copyconst(constituencies)
    for const in all_adj:
        const["num_adj_seats"] += const["num_fixed_seats"]
        const["num_fixed_seats"] = 0
    return all_adj

def set_const_fixed(constituencies):
    all_fixed = copyconst(constituencies)
    for const in all_fixed:
        const["num_fixed_seats"] += const["num_adj_seats"]
        const["num_adj_seats"] = 0
    return all_fixed

def set_copy(constituencies):
    refer = copyconst(constituencies)
    return refer

def set_custom(voteconst, sysconst):
    # Return the constituencies that are in voteconst, but with seat
    # numbers copied from sysconst for those constituencies that are there
    const = copyconst(voteconst)
    sysconstnames = [c["name"] for c in sysconst]
    for k in range(len(const)):
        name = const[k]["name"]
        if name in sysconstnames:
            l = sysconstnames.index(name)
            const[k] = copy(sysconst[l])
    return const
