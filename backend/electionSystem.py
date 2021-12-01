import json
from copy import copy, deepcopy

from system import System
from util import load_constituencies, disp
from dictionaries import DIVIDER_RULES, QUOTA_RULES, RULE_NAMES, ADJUSTMENT_METHODS
from dictionaries import SEAT_SPECIFICATION_OPTIONS

class ElectionSystem(System):
    """A set of rules for an election to follow."""

    def __init__(self):
        super(ElectionSystem, self).__init__()
        self.value_rules = {
            "primary_divider": RULE_NAMES.keys(),
            "adj_determine_divider": RULE_NAMES.keys(),
            "adj_alloc_divider": DIVIDER_RULES.keys(),
            "adjustment_method": ADJUSTMENT_METHODS.keys(),
            "seat_spec_option": SEAT_SPECIFICATION_OPTIONS.keys(),
        }
        self.range_rules = {
            "adjustment_threshold": [0, 100],
            "constituency_threshold": [0, 100],
        }
        self.list_rules = [
            "constituencies", "parties"
        ]
        self["name"] = "System"
        
        # Election systems
        self["primary_divider"] = "1-dhondt"
        self["adj_determine_divider"] = "1-dhondt"
        self["adj_alloc_divider"] = "1-dhondt"
        self["adjustment_threshold"] = 5
        self["constituency_threshold"] = 0
        self["adjustment_method"] = "1-icelandic-law"
        self["seat_spec_option"] = "refer"
        self["compare_with"] = False
        self["parties"] = []

        # Display systems
        self["debug"] = False
        self["show_entropy"] = False
        self["output"] = "simple"

    def __setitem__(self, key, value):
        if key == "constituencies" and type(value) == str:
            value = load_constituencies(value)

        super(ElectionSystem, self).__setitem__(key, value)

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
        option = option.removeprefix("make_")
        sys = (
            deepcopy(self) if option == "refer"
            else self.generate_all_const_system() if option == "all_const"
            else self.generate_all_adj_system() if option == "all_adj"
            else self.generate_one_const_system() if option == "one_const"
            else self.generate_custom_system(vote_table) if option == "custom"
            else None
        )
        return sys

    # def generate_opt_system(self):
    #     system = ElectionSystem()
    #     system.update(self)
    #     system["adjustment_method"] = "B-alternating-scaling"
    #     return system

    # def generate_law_system(self):
    #     system = ElectionSystem()
    #     system.update(self)
    #     system["adjustment_method"] = "1-icelandic-law"
    #     system["primary_divider"] = "1-dhondt"
    #     system["adj_determine_divider"] = "1-dhondt"
    #     system["adj_alloc_divider"] = "1-dhondt"
    #     system["adjustment_threshold"] = 5
    #     system["compare_with"] = False
    #     return system

    def generate_custom_system(self, vote_table):
        system = deepcopy(self)
        set_custom(system["constituencies"], vote_table["constituencies"])
        return system
    
    def generate_one_const_system(self):
        system = deepcopy(self)
        set_one_const(system["constituencies"])
        return system

    def generate_all_adj_system(self):
        system = deepcopy(self)
        set_all_adj(system["constituencies"])
        return system

    def generate_all_const_system(self):
        system = deepcopy(self)
        set_all_const(system["constituencies"])
        return system

def set_one_const(constituencies):
    constituencies[0] = {
        "name": "All",
        "num_const_seats": sum(
            [const["num_const_seats"] for const in constituencies]),
        "num_adj_seats": sum(
            [const["num_adj_seats"] for const in constituencies]),
    }
    del constituencies[1:]

def set_all_adj(constituencies):
    for const in constituencies:
        const["num_adj_seats"] += const["num_const_seats"]
        const["num_const_seats"] = 0

def set_all_const(constituencies):
    for const in constituencies:
        const["num_const_seats"] += const["num_adj_seats"]
        const["num_adj_seats"] = 0

def set_custom(constituencies, customlist):
    # Return the constituencies that are in constituencies, but with seat numbers
    # copied from customlist for those constituencies that are there
    customnames = [c["name"] for c in customlist]
    for k in range(len(constituencies)):
        name = constituencies[k]["name"]
        if name in customnames:
            l = customnames.index(name)
            constituencies[k] = deepcopy(customlist[l])
