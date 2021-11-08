# measureGroups[group][0] is the Group heading (in Excel-file column 1)
# MeasureGroups[group][1][measure][0] is measure title, column 1
# MeasureGroups[group][1][measure][1] is measure title, column 2

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
        self["seatShares"] = [
            "Allocated seats minus reference seat shares",
            {  "sum_abs":  ("Sum of absolute values", ""),
               "sum_pos":  ("Sum of positive values", ""),
               "sum_sq":   ("Sum of squared values", "")}]
        self["other"] = [
            "Specific quality indices for seat allocations",
            {  "entropy":      ("Entropy (logarithmic)", ""),
               "min_seat_val": ("Minimum reference seat share per seat", "")}]
        self["compTitle"] = [
            "Sum of absolute seat allocation differences:",
            {}]
        self["seatSpec"] = [
            "– compared with other seat specifications",
            {  "dev_all_adj":        ("Individual lists", "Only adjustment seats"),
               "dev_all_const":      ("",                 "Only constituency seats"),
               "dev_all_adj_tot":    ("Party totals",     "Only adjustment seats"),
               "dev_all_const_tot":  ("",                 "Only constituency seats"),
               "one_const_tot":      ("",            "All constituencies combined")}]
        self["expected"] = [
            "– compared w. tested systems and source votes",
            {  "dev_ref":     ("Individual lists", ""),
               "dev_ref_tot": ("Party totals", "")}]
        self["cmpSys"] = [
            "– compared with following electoral systems", {}]
        self.add_systems(systems)

    def add_systems(self, systems):
        sysGroup = self["cmpSys"][1]
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

    def get_measures(self, group): # get measures from one group
        return self[group][1].keys()
                
    def get_all_measures(self):  # get measures from all groups
        measures = []
        for value in self.values():
            measures.extend(value[1].keys())
        return measures
    
        group = self.group[grp]
        return group.get_measures()

statisticsHeadings = {
    "avg": "Average of indicated measures for all simulations",
    "std": "Minima for all simulations",
    "min": "Maxima for all simulations",
    "max": "Standard deviations for all simulations",
    "skw": "Skewness for all simulations",
    "kur": "Kurtosis for all simulations"
}
