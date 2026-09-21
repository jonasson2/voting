from copy import copy, deepcopy
#from system import System
#from util import load_constituencies
from apportion import apportion1d_general
from division_rules import adams_gen
from util import remove_prefix
from dictionaries import DEFAULT_ELECTION_SETTINGS, DIVIDER_RULES, QUOTA_RULES
class ElectionSystem(dict):
    """A set of rules for an election to follow."""

    def __init__(self):
        self["name"] = "System"

        self.update(DEFAULT_ELECTION_SETTINGS)
        self["seat_spec_options"] = {"const": "refer", "party": "totals"}
        self["compare_with"] = True
        self["parties"] = []

    def copy_info_from_votes(self, votes):
        self["constituencies"] = deepcopy(votes["constituencies"])
        self["parties"] = deepcopy(votes["parties"])

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
        party_seats = sys['nat_seats']['num_fixed_seats'] + sys['nat_seats']['num_adj_seats'] if \
                sys['nat_seats']['specified'] else None
        if option in {"all_fixed","const_fixed"}:
            sys["constituencies"] = set_const_fixed(self["constituencies"])
            if party_seats and "all_fixed":
                sys['nat_seats'] = set_nat_seats_fixed(self['nat_seats'])
        elif option in {"all_adj", "const_adj"}:
            sys["constituencies"] = set_const_adj(self["constituencies"])
            if party_seats and "all_adj":
                sys['nat_seats'] = set_nat_seats_adj(self['nat_seats'])
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
    nat_seats = {"specified": pvi['specified'],
                 "num_fixed_seats": pvi['num_fixed_seats'],
                 "num_adj_seats": pvi['num_adj_seats']}
    return nat_seats

def set_nat_seats_fixed(pvi):
    nat_seats = {}
    nat_seats['specified'] = True
    nat_seats["num_fixed_seats"] = pvi['num_fixed_seats'] + pvi['num_adj_seats']
    nat_seats["num_adj_seats"] = 0
    return nat_seats

def set_nat_seats_adj(pvi):
    nat_seats = {}
    nat_seats['specified'] = True
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

def set_const_adj_adams(vote_table):
    """Fix the adjustment-seat distribution using constrained Adams."""
    constituencies = copyconst(vote_table["constituencies"])
    pruned = vote_table.get("pruned", [0] * len(constituencies))
    votes = [sum(row) + pruned[c]
             for c, row in enumerate(vote_table["votes"])]
    fixed = [constituency["num_fixed_seats"]
             for constituency in constituencies]
    num_adjustment_seats = vote_table.get(
        "max_total_adj_seats",
        sum(constituency["num_adj_seats"]
            for constituency in constituencies),
    )

    if num_adjustment_seats and not any(votes):
        raise ValueError(
            "Adjustment seats cannot be distributed when all constituency "
            "vote totals are zero.")

    # Under Adams, every positive-vote constituency starts with one seat.
    prior = fixed.copy()
    empty = [c for c, (vote, seats) in enumerate(zip(votes, prior))
             if vote > 0 and seats == 0]
    if len(empty) > num_adjustment_seats:
        raise ValueError(
            "Adams allocation requires an adjustment seat for every "
            "positive-vote constituency with no fixed seats.")
    for c in empty:
        prior[c] = 1

    total_seats = sum(fixed) + num_adjustment_seats
    allocation, _, _ = apportion1d_general(
        votes, total_seats, prior, adams_gen)
    for constituency, fixed_seats, total in zip(
            constituencies, fixed, allocation):
        constituency["num_adj_seats"] = int(total) - fixed_seats
        constituency.pop("max_adj_seats", None)
    return constituencies

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
