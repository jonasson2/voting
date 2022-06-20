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
#   cmp_<systemname>
# and
#   cmp_<systemname>_tot

from util import disp

def funabs(q, s):     return abs(q - s)
def funsq(q, s):      return (q - s)**2
def funpos(q, s):     return max(0, (s - q)/max(1,q))
def funneg(q, s):     return max(0, (s - 1 - q)/max(1,q))
def funsqshare(q, s): return (s - q)**2/max(1,q)
def funsqseat(q, s):  return (s - q)**2/max(1,s)

function_dict = {
    'abs': funabs,
    'sq': funsq,
    'pos': funpos,
    'neg': funneg,
    'sqshare': funsqshare,
    'sqseat': funsqseat,
}

class MeasureGroups(dict):
    def __init__(self, systems, nr=0):
        self["seatShares"] = {
            "title": "Seats minus seat shares, sum over all lists of",
            "rows": {
                "sum_abs":     ("absolute values (Hare-quota)", ""),
                "sum_sq":      ("squared values (Hare-quota)", ""),
                "sum_pos":     ("pos. values scaled by reciprocal shares (D'Hondt)", ""),
                "sum_neg":     ("neg. values scaled by reciprocal shares (D'Hondt)", ""),
                "sum_sqshare": ("sq.val. scaled by reciprocal shares (Sainte-Laguë)", ""),
                "sum_sqseat":  ("sq.val. scaled by reciproc. seats (Hill-Huntington)", ""),
            },
            "footnote": "(single constituency minimizing method in brackets)",            
        }
        self["other"] = {
            "title": "Specific quality indices for seat allocations",
            "rows": {
                "entropy":      ("Sum of logs of votes per seat", ""),
                "min_seat_val": ("Minimum reference seat share per seat", ""),
                "bias_slope":   ("Slope of seat excess regressed on ref. seat shares", ""),
                "bias_corr":    ("Correlation of seat excess and reference seat shares", "")
            }
        }
        self["compTitle"] = {
            "title": "Sum of absolute seat allocation differences:",
            "rows": {}
        }
        self["seatSpec"] = {
            "title": "– compared with other seat specifications",
            "rows": {
                "dev_all_adj":        ("Individual lists", "Only adjustment seats"),
                "dev_all_const":      ("",                 "Only constituency seats"),
                "dev_all_adj_tot":    ("Party totals",     "Only adjustment seats"),
                "dev_all_const_tot":  ("",                 "Only constituency seats"),
                "one_const_tot":      ("",            "All constituencies combined")
            }
        }
        self["expected"] = {
            "title": "– compared w. tested systems and source votes",
            "rows": {
                "dev_ref":     ("Individual lists", ""),
                "dev_ref_tot": ("Party totals", "")
            }
        }
        self["cmpSys"] = {
            "title": "– compared with following electoral systems",
            "rows": {}
        }
        self._add_systems(systems, nr)

    def _add_systems(self, systems, nr=0):
        sysGroup = self["cmpSys"]["rows"]
        firstcol = "Individual lists"
        for sys in systems:
            p = "compare_with" in sys
            if not p:
                raise ValueError
            compare = sys["compare_with"]
            if sys["compare_with"]:
                measure = "cmp_" + sys["name"]
                sysGroup[measure] = (firstcol, sys["name"])
                firstcol = ""
        firstcol = "Party totals"
        for sys in systems:
            if sys["compare_with"]:
                measure = "cmp_" + sys["name"] + "_tot"
                sysGroup[measure] = (firstcol, sys["name"])
                firstcol = ""
        no_comparison_systems = not sysGroup
        if no_comparison_systems:
            del self["cmpSys"]
            return

    def get_measures(self, group): # get measures from one group
        return self[group]["rows"].keys()
                
    def get_all_measures(self):  # get measures from all groups
        measures = []
        for value in self.values():
            measures.extend(value["rows"].keys())
        return measures
    
        group = self.group[grp]
        return group.get_measures()

headingType = {
    "seatShares": "systems",
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
