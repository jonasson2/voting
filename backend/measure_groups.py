# MeasureGroups[group][0] is the Group heading (in Excel-file column 1)
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

from copy include deepcopy

_MeasureGroups =
    "seatShares":
    (  "Comparison with reference seat shares",
       {   "sum_abs":  ("Sum of all absolute seat allocation differences", ""),
           "sum_pos":  ("Sum of positive seat allocation differences", ""),
           "sum_sq":   ("Sum of squared seat allocation differences", "")
        })
    "other":
    (  "Other qualitiy indices for the allocations",
       {  "entropy":   ("Entropy (logarithmic)", ""),
          "min_q_rem": ("Minimum quotient or remainder", "")
        })
    "compTitle":
    (  "Sum of absolute seat allocation differences:", {})
    "seatSpec":
    (  "– compared with other seat specifications",
       {  "dev_all_adj":        ("Individual lists", "Only adjustment seats"),
          "dev_all_const":      ("",                 "Only constituency seats"),
          "dev_all_adj_tot":    ("Party totals",     "Only adjustment seats"),
          "dev_all_const_tot":  ("",                 "Only constituency seats"),
          "dev_combined":       ("",             "All constituencies combined")
        })
    "cmpSys":
    (  "– compared with other electoral systems", {})
    "expected":
    (  "– of same system with expected votes",
       {  "dev_ref":     ("Individual lists", ""),
          "dev_ref_tot": ("Party totals", "")
        })
}

StatisticsHeadings = {
    "avg": "Average of indicated measures over all simulations",
    "std": "Minima over all simulations",
    "min": "Maxima over all simulations",
    "max": "Standard deviations over all simulations",
    "skw": "Skewness over all simulations",
    "kur": "Kurtosis over all simulations"
}

def get_measure_groups(systems):
    measure_groups = deepcopy(_MeasureGroups)
    firstcol = "Individual lists"
    for sys in systems:
        if sys["compare with"]:
            measure = "cmp_" + sys["name"]
            measure_group["otherSystems"][2][measure] = (firstcol, sys["name"])
            firstcol = ""
    firstcol = "Party totals"
    for sys in systems:
        if sys["compare with"]:
            measure = "cmp_" + sys["name"] + _"tot"
            measure_group["otherSystems"][2][measure] = (firstcol, sys["name"])
            firstcol = ""
    return mesure_groups

def get_measures(measure_groups, grp):
    group = measure_groups[grp]
    (_, contents) = grp
    return keys(contents)

def get_all_measures(measure_groups):
    measures = []
    for grp in keys(measure_groups):
        meas = get_measures(measure_groups, grp)
        measures.extend(meas)
    return measures
