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
STRUCTURAL_ZERO_GROUPS = {"cmpList", "cmpParty"}
WEB_STD_GROUPS = {
    "shareTitle", "toLists", "toPartiesTotal", "other",
}

def combine_titles(titles, last_column1):
    (column1, column2) = titles
    if not column1:
        column1 = last_column1       
    title = column1 + (": " + column2 if column2 else "")
    return title, column1

def normalize_negative_zero(value):
    return 0 if -1e-8 < value < 0 else value


def _system_display_value(
        data, system_index, measure, stat, group, nsim,
        entropy_score_available):
    if (measure == "entropy_score"
            and not entropy_score_available[system_index]):
        return "–"
    value = normalize_negative_zero(
        data[system_index]["measures"][measure][stat])
    result = {
        "value": value,
        "integer": fractional_digits(group, stat) == 0,
        "ci": None,
    }
    if measure == "entropy_score":
        result["percentage"] = True
    if stat == "avg" and nsim > 0:
        std = data[system_index]["measures"][measure]["std"]
        result["ci"] = 1.96 * std / sqrt(nsim)
    return result


def _paired_display_value(
        paired_data, measure, group, nsim, entropy_score_available):
    if (measure == "entropy_score"
            and not all(entropy_score_available[:2])):
        return "–"
    paired = paired_data.get(measure)
    show = group not in {"cmpList", "cmpParty", "cmpNationalDetails"}
    value = normalize_negative_zero(paired["avg"]) if paired and show else 0
    ci = (
        1.96 * paired["std"] / sqrt(nsim)
        if paired and show and nsim > 0 else None
    )
    result = {"value": value, "integer": False, "ci": ci}
    if measure == "entropy_score":
        result["percentage"] = True
    return result


def _measure_row(
        data, systems, paired_data, group, measure, title, nsim,
        entropy_score_available):
    row = {"rowtitle": title}
    if measure == "entropy_score":
        row["rowtitle"] += " (%)"
        row["tooltip"] = (
            "The product of the allocated-seat quotients divided by the "
            "largest achievable product under the selected rule and "
            "constraints. 100% is optimal; the Difference column is in "
            "percentage points.")
    elif measure == "constituency_disparity":
        row["tooltip"] = (
            "Highest constituency votes per seat divided by lowest. "
            "Includes votes for parties without seats and pruned votes; "
            "1 means equal votes per seat.")
    has_paired_difference = (
        len(systems) >= 2 and group not in NO_PAIRED_DIFFERENCE_GROUPS)
    for stat in STATISTICS_HEADINGS:
        row[stat] = [
            "" if (group in STRUCTURAL_ZERO_GROUPS
                   and system["name"] == title) else
            _system_display_value(
                data, index, measure, stat, group, nsim,
                entropy_score_available)
            for index, system in enumerate(systems)
        ]
        if stat == "avg" and has_paired_difference:
            row[stat].insert(
                2, _paired_display_value(
                    paired_data, measure, group, nsim,
                    entropy_score_available))
    return row


def _vue_data_header(systems):
    names = [system["name"] for system in systems]
    web_statistics = ["avg", "std"]
    result = {
        "stats": web_statistics,
        "stat_headings": {
            statistic: STATISTICS_HEADINGS[statistic]
            for statistic in web_statistics
        },
        "headingType": dict(headingType),
        "system_names": names,
        "has_paired_difference": len(systems) >= 2,
        "groups_without_paired_difference": sorted(
            NO_PAIRED_DIFFERENCE_GROUPS),
        "group_ids": [],
        "group_stats": {},
        "group_titles": {
            "topLeft": (
                "Differences between allocated and fractional reference\n"
                "seat shares, summed over constituency lists"
            )
        },
        "group_messages": {},
        "footnotes": {},
        "show": {},
    }
    if len(systems) >= 2:
        result["difference_tooltip"] = (
            f"Absolute difference between {names[0]} and {names[1]}, "
            "calculated separately for each simulated election."
        )
    return result


def _add_sensitivity_vuedata(vuedata, sensitivity_data, systems, nsim):
    if not sensitivity_data:
        return
    groups = (
        ("sensitivityWithin", "sensitivity_within_parties",
         "Seats displaced between lists within parties"),
        ("sensitivityBetween", "sensitivity_between_parties",
         "Seats displaced between parties"),
    )
    nsys = len(systems)
    for group_id, measure, title in groups:
        vuedata["group_ids"].append(group_id)
        vuedata["group_titles"][group_id] = title
        vuedata["headingType"][group_id] = (
            "empty" if group_id == "sensitivityBetween" else "systems")
        vuedata["group_stats"][group_id] = ["avg"]
        vuedata["show"][group_id] = True
        vuedata[group_id] = []
        for row_index, cov in enumerate(sensitivity_data["covs"]):
            row = {"rowtitle": f"{cov:g}% CoV"}
            for statistic in vuedata["stats"]:
                values = sensitivity_data[measure][statistic][row_index]
                displayed = list(values[:nsys])
                indices = list(range(nsys))
                if statistic == "avg" and nsys >= 2:
                    displayed.insert(2, values[-1])
                    indices.insert(2, -1)
                row[statistic] = []
                for value, value_index in zip(displayed, indices):
                    entry = {
                        "value": normalize_negative_zero(value),
                        "integer": False,
                        "ci": None,
                    }
                    if statistic == "avg" and nsim > 0:
                        std = sensitivity_data[measure]["std"][row_index][
                            value_index]
                        entry["ci"] = 1.96 * std / sqrt(nsim)
                    row[statistic].append(entry)
            vuedata[group_id].append(row)


def add_vuedata(sim_result_dict, parallel):
    data = sim_result_dict["data"]
    if not data:
        return
    party_votes_specified = sim_result_dict["vote_table"]["party_vote_info"]["specified"]
    systems = sim_result_dict["systems"]
    include_entropy_score = sim_result_dict.get("sim_settings", {}).get(
        "entropy_score", False)
    groups = MeasureGroups(
        systems, party_votes_specified, "",
        include_entropy_score=include_entropy_score)
    nsim = sim_result_dict["iteration"]
    paired_data = sim_result_dict.get("paired_data", {})
    entropy_score_available = sim_result_dict.get(
        "entropy_score_available", [True] * len(systems))
    vuedata = _vue_data_header(systems)
    for (id, group) in groups.items():
        vuedata["group_ids"].append(id)
        vuedata["group_titles"][id] = group["title"]
        if id not in WEB_STD_GROUPS:
            vuedata["group_stats"][id] = ["avg"]
        last_column1 = ""
        vuedata[id] = []
        if "footnote" in group:
            vuedata["footnotes"][id] = group["footnote"]
        vuedata["show"][id] = not ("onlyExcel" in group and group["onlyExcel"])
        for (measure, titles) in group["rows"].items():
            (rowtitle, last_column1) = combine_titles(titles, last_column1)
            row = _measure_row(
                data, systems, paired_data, id, measure, rowtitle, nsim,
                entropy_score_available)
            if vuedata[id] and measure in group.get("subgroup_starts", ()):
                row["subgroup_start"] = True
            vuedata[id].append(row)
    if len(systems) < 2:
        for group_id in ("cmpListTitle", "cmpList", "cmpPartyTitle", "cmpParty"):
            vuedata["show"][group_id] = False
    elif "cmpParty" in groups:
        # Check maxima so even a rare difference keeps the comparison visible.
        has_party_difference = any(
            system_data["measures"][measure]["max"] != 0
            for system_data in data
            for measure in groups["cmpParty"]["rows"])
        if not has_party_difference:
            vuedata["show"]["cmpParty"] = False
            vuedata["group_messages"]["cmpPartyTitle"] = (
                "All tested systems gave identical party seat totals "
                "in this simulation.")
    _add_sensitivity_vuedata(
        vuedata, sim_result_dict.get("sensitivity_data"), systems, nsim)
    sim_result_dict["vuedata"] = vuedata

# Statistic ids are an array in                        vuedata["stats"]
# Statistic headings are a dictionary stat–>heading in vuedata["stat_headings"]
# System names are an array in                         vuedata["system_names"]
# Group ids are an array in                            vuedata["group_ids"]
# Group titles are a dictionary id–>title in           vuedata["group_titles"]
# Row titles are in                    vuedata[groupid][row]["rowtitle"], row=0,1,2...
# The resulting statistics are in      vuedata[groupid][row][stat][s], s=0,1,...,nsys-1
