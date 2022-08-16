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
    def __init__(self, systems, party_votes_specified, nr=0):
        self["shareTitle"] = {
            "title": "Seats minus seat shares, sum over allocations to:",
            "rows":  {}
        }

        self["toLists"] = {
            "title": "– constituency lists",
            "rows": {
                "sum_abs":     ("absolute values (Hare-quota)", ""),
                "sum_sq":      ("squared values (Hare-quota)", ""),
                "sum_pos":     ("pos. values scaled by reciprocal shares (D'Hondt)", ""),
                "sum_neg":     ("neg. values scaled by reciprocal shares (Adams)", ""),
                "sum_absshare": ("abs. values scaled by reciprocal share (Sainte-Laguë)", ""),
                "sum_sqshare": ("sq.val. scaled by reciprocal shares (Sainte-Laguë)", ""),
                "sum_sqseat":  ("sq.val. scaled by reciprocal seats (Hill-Huntington)", ""),
            },
            "footnote": "(single constituency minimizing method in brackets)",            
        }

        if party_votes_specified:
            self["toPartiesInConst"] = {
                "title": "– parties in the constituencies",
                
                "rows": {
                    "sum_abs_party": ("sum of absolute values",""),
                    "sum_sq_party": ("sum of squared values",""),
                },
                "onlyExcel": True
            }

            self["toNationalLists"] = {
                "title": "– national lists",
                "rows": {
                    "sum_abs_party": ("sum of absolute values",""),
                    "sum_sq_party": ("sum of squared values",""),
                },
                "onlyExcel": True
            }

        self["toPartiesTotal"] = {
            "title": "– parties overall" if party_votes_specified else "– party totals",
            # overall,
            # altogeter, grand total
            "rows": {
                "sum_abs_party": ("sum of absolute values",""),
                "sum_sq_party":  ("sum of squared values",""),
                "max_val_party": ("maximum value", ""),
                "min_val_party": ("minimum value", ""),
            }
        }

        self["other"] = {
            "title": "Specific quality indices for allocations in the constituencies",
            "rows": {
                "entropy":        ('Sum of logs of votes per seat ("entropy")', ""),
                "min_seat_val":   ("Minimum reference seat share per seat", ""),
                "max_neg_margin": ("Maximum negative margin over constituencies",""),
                "avg_neg_margin": ("Average negative margin over constituencies",""),
                "bias_slope":     ("Slope of seat excess regressed on ref. seat shares", ""),
                "bias_corr":      ("Correlation of seat excess and reference seat "
                                   "shares", ""),
                "disparity":      ("Total and reference allocations abs. difference", ""),
                "excess":         ("Excess", ""),
                "shortage":       ("Shortage", "")
            }
        }

        self["compTitle"] = {
            "title": "Sum of absolute seat allocation differences over:",
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
        self["cmpSys"] = {
            "title": "– compared with following electoral systems",
            "rows": {}
        }
        self._add_systems(systems, party_votes_specified, nr)

    def _add_systems(self, systems, party_votes_specified, nr=0):
        sysGroup = self["cmpSys"]["rows"]
        firstcol = "Constituency lists"
        for sys in systems:
            p = "compare_with" in sys
            if not p:
                raise ValueError
            compare = sys["compare_with"]
            if sys["compare_with"]:
                measure = "cmp_" + sys["name"] + "_const"
                sysGroup[measure] = (firstcol, sys["name"])
                firstcol = ""
        firstcol="party constituency totals" if party_votes_specified else "party totals"
        for sys in systems:
            if sys["compare_with"]:
                measure = "cmp_" + sys["name"] + "_tot"
                sysGroup[measure] = (firstcol, sys["name"])
                firstcol = ""
        if party_votes_specified:
            firstcol = "national lists"
            for sys in systems:
                if sys["compare_with"]:
                    measure = "cmp_" + sys["name"] + "_nat"
                    sysGroup[measure] = (firstcol, sys["name"])
                    firstcol = ""
            firstcol = "party grand totals"
            for sys in systems:
                if sys["compare_with"]:
                    measure = "cmp_" + sys["name"] + "_grand"
                    sysGroup[measure] = (firstcol, sys["name"])
                    firstcol = ""
        no_comparison_systems = not sysGroup
        if no_comparison_systems:
            del self["cmpSys"]
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
    "compTitle":  "stats",
    "seatSpec":   "systems",
    "expected":   "empty",
    "cmpSys":     "empty"
}

def fractional_digits(group, stat):
    if group in {"seatSpec", "expected", "cmpSys"} and stat in {"min", "max"}:
        return 0
    else:
        return 3
