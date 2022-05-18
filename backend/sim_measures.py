# Construct titles and data to put in the measures table in
# simulation results

from measure_groups import MeasureGroups, fractional_digits
from measure_groups import headingType
from dictionaries import STATISTICS_HEADINGS
from util import disp
from copy import deepcopy
from math import sqrt

def combine_titles(titles, last_column1):
    (column1, column2) = titles
    if not column1:
        column1 = last_column1       
    title = column1 + (": " + column2 if column2 else "")
    return title, column1

def add_vuedata(sim_result_dict, parallel):
    data = sim_result_dict["data"]
    if not data:
        return
    systems = sim_result_dict["systems"]
    groups = MeasureGroups(systems)
    stats = list(STATISTICS_HEADINGS(parallel).keys())
    nsys = len(systems)
    nsim = sim_result_dict["iteration"]
    vuedata = {}
    vuedata["stats"] = stats
    vuedata["stat_headings"] = STATISTICS_HEADINGS(parallel)
    vuedata["headingType"] = headingType
    vuedata["system_names"] = [sys["name"] for sys in systems]
    vuedata["group_ids"] = []
    vuedata["group_titles"] = {}
    vuedata["footnotes"] = {}
    for (id, group) in groups.items():
        vuedata["group_ids"].append(id)
        vuedata["group_titles"][id] = group["title"]
        last_column1 = ""
        vuedata[id] = []
        if "footnote" in group:
            vuedata["footnotes"][id] = group["footnote"]
        for (measure, titles) in group["rows"].items():
            (rowtitle, last_column1) = combine_titles(titles, last_column1)
            row = {"rowtitle": rowtitle}
            for stat in stats:
                row[stat] = []
                for s in range(len(systems)):
                    entry = data[s]["measures"][measure][stat]
                    ndig = 0 if entry == 0 else fractional_digits(id, stat)
                    row[stat].append(f"{entry:.{ndig}f}")
                    if stat == "avg" and entry != 0:
                        std = data[s]["measures"][measure]["std"]
                        CI = 1.96*std/sqrt(nsim)
                        row[stat][-1] += f" ± {CI:.{ndig}f}"
            vuedata[id].append(row)            
    sim_result_dict["vuedata"] = vuedata

# Statistic ids are an array in                        vuedata["stats"]
# Statistic headings are a dictionary stat–>heading in vuedata["stat_headings"]
# System names are an array in                         vuedata["system_names"]
# Group ids are an array in                            vuedata["group_ids"]
# Group titles are a dictionary id–>title in           vuedata["group_titles"]
# Row titles are in                    vuedata[groupid][row]["rowtitle"], row=0,1,2...
# The resulting statistics are in      vuedata[groupid][row][stat][s], s=0,1,...,nsys-1
