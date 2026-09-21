# Construct titles and data to put in the measures table in
# simulation results

from measure_groups import MeasureGroups, fractional_digits
from measure_groups import headingType
from dictionaries import STATISTICS_HEADINGS
from util import disp
from copy import deepcopy
from math import sqrt


NO_PAIRED_DIFFERENCE_GROUPS = {
    "cmpListTitle", "cmpList", "cmpPartyTitle", "cmpParty",
    "cmpNationalDetails",
}

def combine_titles(titles, last_column1):
    (column1, column2) = titles
    if not column1:
        column1 = last_column1       
    title = column1 + (": " + column2 if column2 else "")
    return title, column1

def normalize_negative_zero(value):
    return 0 if -1e-8 < value < 0 else value


def _system_display_value(data, system_index, measure, stat, group, nsim):
    value = normalize_negative_zero(
        data[system_index]["measures"][measure][stat])
    result = {
        "value": value,
        "integer": fractional_digits(group, stat) == 0,
        "ci": None,
    }
    if stat == "avg" and nsim > 0:
        std = data[system_index]["measures"][measure]["std"]
        result["ci"] = 1.96 * std / sqrt(nsim)
    return result


def _paired_display_value(paired_data, measure, group, nsim):
    paired = paired_data.get(measure)
    show = group not in {"cmpList", "cmpParty", "cmpNationalDetails"}
    value = normalize_negative_zero(paired["avg"]) if paired and show else 0
    ci = (
        1.96 * paired["std"] / sqrt(nsim)
        if paired and show and nsim > 0 else None
    )
    return {"value": value, "integer": False, "ci": ci}


def _measure_row(data, systems, paired_data, group, measure, title, nsim):
    row = {"rowtitle": title}
    has_paired_difference = (
        len(systems) >= 2 and group not in NO_PAIRED_DIFFERENCE_GROUPS)
    for stat in STATISTICS_HEADINGS:
        row[stat] = [
            _system_display_value(data, index, measure, stat, group, nsim)
            for index in range(len(systems))
        ]
        if stat == "avg" and has_paired_difference:
            row[stat].insert(
                2, _paired_display_value(paired_data, measure, group, nsim))
    return row


def _vue_data_header(systems):
    names = [system["name"] for system in systems]
    result = {
        "stats": list(STATISTICS_HEADINGS),
        "stat_headings": STATISTICS_HEADINGS,
        "headingType": headingType,
        "system_names": names,
        "has_paired_difference": len(systems) >= 2,
        "groups_without_paired_difference": sorted(
            NO_PAIRED_DIFFERENCE_GROUPS),
        "group_ids": [],
        "group_titles": {
            "topLeft": (
                "Differences between allocated and fractional\n"
                "reference seats, summed over constituency lists"
            )
        },
        "footnotes": {},
        "show": {},
    }
    if len(systems) >= 2:
        result["difference_tooltip"] = (
            f"{names[0]} minus {names[1]}, calculated separately for each "
            "simulated election."
        )
    return result


def add_vuedata(sim_result_dict, parallel):
    data = sim_result_dict["data"]
    if not data:
        return
    party_votes_specified = sim_result_dict["vote_table"]["party_vote_info"]["specified"]
    systems = sim_result_dict["systems"]
    groups = MeasureGroups(systems, party_votes_specified, "")
    nsim = sim_result_dict["iteration"]
    paired_data = sim_result_dict.get("paired_data", {})
    vuedata = _vue_data_header(systems)
    for (id, group) in groups.items():
        vuedata["group_ids"].append(id)
        vuedata["group_titles"][id] = group["title"]
        last_column1 = ""
        vuedata[id] = []
        if "footnote" in group:
            vuedata["footnotes"][id] = group["footnote"]
        vuedata["show"][id] = not ("onlyExcel" in group and group["onlyExcel"])
        for (measure, titles) in group["rows"].items():
            (rowtitle, last_column1) = combine_titles(titles, last_column1)
            vuedata[id].append(_measure_row(
                data, systems, paired_data, id, measure, rowtitle, nsim))
    sim_result_dict["vuedata"] = vuedata

# Statistic ids are an array in                        vuedata["stats"]
# Statistic headings are a dictionary stat–>heading in vuedata["stat_headings"]
# System names are an array in                         vuedata["system_names"]
# Group ids are an array in                            vuedata["group_ids"]
# Group titles are a dictionary id–>title in           vuedata["group_titles"]
# Row titles are in                    vuedata[groupid][row]["rowtitle"], row=0,1,2...
# The resulting statistics are in      vuedata[groupid][row][stat][s], s=0,1,...,nsys-1
