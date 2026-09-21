# measureGroups[group]["title"] is the Group heading (in Excel-file column 1)
# MeasureGroups[group]["rows"][measure][0] is measure title, column 1
# MeasureGroups[group]["rows"][measure][1] is measure title, column 2

# Corresponding data is stored in
#   simulation.data[r][m][stat]
# where:
#   r ranges over 0...num_systems-1 (number of electoral systems being simulated)
#   m ranges over the measures, and,
#   stat ranges over "avg", "std", "min", "max", "skw" and "kur"
#
# The system names are in
#   simulation.systems[r].name (r=0,1,...)
#
# The measure-names for comparison with other systems are:
#   cmp_<systemname>_const
#   cmp_<systemname>_tot
#   cmp_<systemname>_nat
# and
#   cmp_<systemname>_grand


from util import disp

def funabs(h, s):      return abs(h - s)
def funsq(h, s):       return (h - s)**2
def funpos(h, s):      return max(0, (s - h))/h
def funneg(h, s):      return max(0, (h - s))/h
def funabsshare(h, s): return abs(h - s)/h
def funsqshare(h, s):  return (s - h)**2/h
def funsqseat(h, s):   return (s - h)**2/max(1,s) if s > 0 else 0
def funsame(h,s):      return s - h

function_dict = {
    'abs': (funabs, False),
    'sq': (funsq, False),
    'pos': (funpos, True),
    'neg': (funneg, True),
    'absshare': (funabsshare, True),
    'sqshare': (funsqshare, True),
    'sqseat': (funsqseat, False)
}

function_dict_party = {
    'sum_abs_party': (funabs),
    'sum_sq_party': (funsq),
    'max_val_party': (funsame),
    'min_val_party': (funsame),
}

class MeasureGroups(dict):
    def __init__(self, systems, party_votes_specified, qm_topleft2=None, nr=0):
        self["shareTitle"] = {
            "title": qm_topleft2,
            "rows":  {}
        }

        self["toLists"] = {
            "title": "",
            "rows": {
                "sum_abs":     ("Absolute values (Hare quota)", ""),
                "sum_sq":      ("Squared values (Hare quota)", ""),
                "sum_pos":     ("Over-allocation per reference seat", ""),
                "sum_neg":     ("Under-allocation per reference seat", ""),
                "sum_absshare": ("Absolute values per reference seat", ""),
                "sum_sqshare": ("Squared values per reference seat (Sainte-Laguë)", ""),
                "sum_sqseat":  ("Squared values per allocated seat", ""),
            },
            "footnote": "(single constituency minimizing methods in brackets)",
        }

        if party_votes_specified:
            self["toPartiesInConst"] = {
                "title": "– parties in the constituencies",
                
                "rows": {
                    "sum_abs_party_const": ("sum of absolute values",""),
                    "sum_sq_party_const": ("sum of squared values",""),
                },
                "onlyExcel": True
            }

            self["toNationalLists"] = {
                "title": "– national lists",
                "rows": {
                    "sum_abs_party_nat": ("sum of absolute values",""),
                    "sum_sq_party_nat": ("sum of squared values",""),
                },
                "onlyExcel": True
            }

        self["toPartiesTotal"] = {
            "title": "Party seat totals: allocated minus fractional reference",
            # overall,
            # altogeter, grand total
            "rows": {
                "sum_abs_party_overall": ("sum of absolute values",""),
                "sum_sq_party_overall":  ("sum of squared values",""),
                "max_val_party_overall": ("maximum value", ""),
                "min_val_party_overall": ("minimum value", ""),
            }
        }

        self["other"] = {
            "title": "Specific quality indices for allocations in the constituencies",
            "rows": {
                "entropy_dhondt": ("D'Hondt entropy", ""),
                "entropy_sainte_lague": ('Sainte-Laguë entropy', ""),
                "max_overrepresentation": (
                    "Greatest relative over-representation (D'Hondt)", ""),
                "max_underrepresentation": (
                    "Greatest relative under-representation (Adams)", ""),
                "max_neg_margin": ("Maximum negative margin over constituencies",""),
                "freq_neg_margin": ("Frequency of negative margin over constituencies",""),
                "bias_slope":     ("Slope of seat excess regressed on ref. seat shares", ""),
                "bias_corr":      ("Correlation of seat excess and reference seat "
                                   "shares", ""),
                "geographical_displacement": (
                    "Geographical seat displacement", ""),
                #"disparity":      ("Total and reference allocations abs. difference",""),
                "excess":         ("Total seat excess", ""),
                "total_overhang": ("Potential overhang", ""),
                #"shortage":       ("Shortage", "")
            },
            "footnote": "(single-constituency minimizing methods in brackets)",
        }

        self["cmpListTitle"] = {
            "title": "Absolute seat differences summed over constituency lists",
            "onlyExcel": False,
            "rows": {}
        }
        self["seatSpec"] = {
            "title": "– compared with other seat specifications",
            "rows": {
                "dev_all_adj_const":   ("constituency lists", "all seats as adjustment seats"),
                "dev_all_fixed_const": ("",                 "all seats as fixed seats"),
                "dev_all_adj_tot":     ("party constituency totals","all seats as adjustment seats"),
                "dev_all_fixed_tot":   ("",                 "all seats as fixed seats"),
                "dev_all_adj_nat":     ("national lists",   "all seats as adjustment seats"),
                "dev_all_fixed_nat":   ("",                 "all seats as fixed seats"),
                "dev_all_adj_grand":   ("party grand totals", "all seats as adjustment seats"),
                "dev_all_fixed_grand": ("",                 "all seats as fixed seats"),
                "one_const_tot":       ("",                 "All constituencies combined")
            } if party_votes_specified else {
                "dev_all_adj_const":   ("constituency lists", "all seats as adjustment seats"),
                "dev_all_fixed_const": ("",                 "all seats as fixed seats"),
                "dev_all_adj_tot":     ("party totals","all seats as adjustment seats"),
                "dev_all_fixed_tot":   ("",                 "all seats as fixed seats"),
                "one_const_tot":       ("",                 "All constituencies combined")
            },
            "onlyExcel": True
        }
        self["expected"] = {
            "title": "– compared w. tested systems and source votes",
            "rows": {
                "dev_ref_const": ("constituency lists", ""),
                "dev_ref_tot":   ("party constituency totals", ""),
                "dev_ref_nat":   ("national lists", ""),
                "dev_ref_grand": ("party grand totals", ""),
            } if party_votes_specified else {
                "dev_ref_const": ("constituency lists", ""),
                "dev_ref_tot":   ("party totals", ""),
            },
            "onlyExcel": True
        }
        self["cmpList"] = {
            "title": "",
            "rows": {}
        }
        self["cmpPartyTitle"] = {
            "title": "Absolute seat differences summed over parties",
            "rows": {}
        }
        self["cmpParty"] = {
            "title": "",
            "rows": {}
        }
        if party_votes_specified:
            self["cmpNationalDetails"] = {
                "title": "Additional national-vote comparison details",
                "rows": {},
                "onlyExcel": True,
            }
        self._add_systems(systems, party_votes_specified, nr)

    def _add_systems(self, systems, party_votes_specified, nr=0):
        list_group = self["cmpList"]["rows"]
        party_group = self["cmpParty"]["rows"]
        for sys in systems:
            if "compare_with" not in sys:
                raise ValueError
            if sys["compare_with"]:
                measure = "cmp_" + sys["name"] + "_const"
                list_group[measure] = (sys["name"], "")
        for sys in systems:
            if sys["compare_with"]:
                suffix = "grand" if party_votes_specified else "tot"
                measure = "cmp_" + sys["name"] + "_" + suffix
                party_group[measure] = (sys["name"], "")
        if party_votes_specified:
            details = self["cmpNationalDetails"]["rows"]
            for sys in systems:
                if sys["compare_with"]:
                    name = sys["name"]
                    details["cmp_" + name + "_tot"] = (
                        "Party constituency totals", name)
                    details["cmp_" + name + "_nat"] = (
                        "National lists", name)
        no_comparison_systems = not list_group
        if no_comparison_systems:
            for group in ("cmpListTitle", "cmpList", "cmpPartyTitle", "cmpParty",
                          "cmpNationalDetails"):
                self.pop(group, None)
            return

    def get_measures(self, group): # get measures from one group
        return self[group]["rows"].keys()
                
    def get_all_measures(self, party_votes_specified):  # get measures from all groups
        measures = []
        for value in self.values():
            add = [x for x in value["rows"].keys()
                   # næsta if þarf hugsanlega ekki
                if party_votes_specified or not x.endswith(('_nat', '_grand'))]
            measures.extend(add)
        return measures

headingType = {
    "shareTitle": "systems",
    "toLists": "empty",
    "toPartiesInConst": "empty",
    "other":      "empty",
    "cmpListTitle": "stats",
    "cmpList":      "systems",
    "cmpPartyTitle": "empty",
    "cmpParty":      "empty",
    "seatSpec":   "systems",
    "expected":   "empty",
    "cmpNationalDetails": "empty"
}

def fractional_digits(group, stat):
    if group in {"seatSpec", "expected", "cmpList", "cmpParty",
                 "cmpNationalDetails"} and stat in {"min", "max"}:
        return 0
    else:
        return 3
