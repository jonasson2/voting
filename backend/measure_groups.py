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

class MeasureGroups(dict):
    def __init__(self, systems):
        self["seatShares"] = {
            "title": "Allocated seats minus reference seat shares",
            "rows": {
                "sum_abs":  ("Sum of absolute values", ""),
                "sum_pos":  ("Sum of positive values", ""),
                "sum_sq":   ("Sum of squared values", "")
            }
        }
        self["other"] = {
            "title": "Specific quality indices for seat allocations",
            "rows": {
                "entropy":      ("Entropy (logarithmic)", ""),
                "min_seat_val": ("Minimum reference seat share per seat", "")
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
        self._add_systems(systems)

    def _add_systems(self, systems):
        sysGroup = self["cmpSys"]["rows"]
        firstcol = "Individual lists"
        for sys in systems:
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

statisticsHeadings = {
    # "avg": "Averages for all simulations",
    # "min": "Maxima for all simulations",
    # "max": "Standard deviations for all simulations",
    # "std": "Minima for all simulations",
    # "skw": "Skewness for all simulations",
    # "kur": "Kurtosis for all simulations"
    "avg": "AVERAGE",
    "min": "MINIMUM",
    "max": "MAXIMUM",
    "std": "STD.DEV.",
    "skw": "SKEWNESS",
    "kur": "KURTOSIS"
}

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
