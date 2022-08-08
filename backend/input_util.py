import os
from distutils.util import strtobool
from copy import deepcopy
from util import disp

def check_input(data, sections):
    for section in sections:
        if section not in data or not data[section]:
            print("raising error")
            raise KeyError(f"Missing data ('{section}')")
    return data

def check_vote_table(vote_table):
    table = deepcopy(vote_table)
    for info in [
        "name",
        "votes",
        "parties",
        "constituencies",
    ]:
        if info not in table or not table[info]:
            raise KeyError(f"Missing data ('vote_table.{info}')")

    num_parties = len(table["parties"])
    num_constituencies = len(table["constituencies"])

    if not len(table["votes"]) == num_constituencies:
        raise ValueError("The vote table does not match the constituency list.")
    for row in table["votes"]:
        if not len(row) == num_parties:
            raise ValueError("The vote table does not match the party list.")
        for p in range(len(row)):
            if not row[p]: row[p] = 0
            if row[p] < 0:
                raise ValueError("Votes may not be negative.")
    if "party_votes" in table:
        table["party_vote_info"] = table["party_votes"]
        del table["party_votes"]

    for const in table["constituencies"]:
        if "name" not in const:  # or not const["name"]:
            raise KeyError(f"Missing data ('vote_table.constituencies[x].name')")
        if "num_fixed_seats" not in const:
            const["num_fixed_seats"] = const["num_const_seats"]
            del const["num_const_seats"]
        name = const["name"]
        for info in ["num_fixed_seats", "num_adj_seats"]:
            if info not in const:
                raise KeyError(f"Missing data ('{info}' for {name})")
            if not const[info]: const[info] = 0
            if type(const[info]) != int:
                raise TypeError("Seat specifications must be numbers.")

    seen = set()
    for const in table["constituencies"]:
        if False:  # const["name"] in seen:
            raise ValueError("Constituency names must be unique. "
                             f"{const['name']} is not.")
        seen.add(const["name"])

    return table

def check_systems(electoral_systems):
    """Checks election systems constituency input, and translates empty cells to 0

    Raises:
        KeyError: If constituencies are missing a component
        TypeError: If seat counts are not given as numbers
        ValueError: If not enough seats are specified
    """
    if not electoral_systems:
        raise ValueError("Must have at least one electoral system.")
    electoral_systems = [e for e in electoral_systems if e["name"] != "Monge"]
    # Monge is iffy and thus removed
    for electoral_system in electoral_systems:
        if "compare_with" not in electoral_system:
            electoral_system["compare_with"] = False
        for const in electoral_system["constituencies"]:
            if 'num_const_seats' in const:
                const['num_fixed_seats'] = const['num_const_seats']
                del const['num_const_seats']
            if "name" not in const:  # or not const["name"]:
                # can never happen in case of input from frontend
                raise KeyError(f"Missing data ('constituencies[x].name' in "
                               f"electoral system {electoral_system['name']})")
            name = const["name"]
            for info in ["num_fixed_seats", "num_adj_seats"]:
                if info not in const:
                    raise KeyError(f"Missing data ('{info}' for {name} in "
                                   f"electoral system {electoral_system['name']})")
                if not const[info]: const[info] = 0
                if type(const[info]) != int:
                    raise TypeError("Seat specifications must be numbers.")
            # if (const["num_fixed_seats"] + const["num_adj_seats"] <= 0):
            #     raise ValueError("Fixed seats and adjustment seats "
            #          "must add to a nonzero number. "
            #          f"This is not the case for {name} in "
            #          f"electoral system {electoral_system['name']}.")
    return electoral_systems

def check_simul_settings(sim_settings):
    from math import sqrt
    """Checks simulation settings, and translates checkbox values to bool values

    Raises:
        KeyError: If simulation settings are missing a component
        ValueError: If coefficient of variation is too high
    """
    if "row_constraints" in sim_settings and "col_constraints" in sim_settings:
        for key in ["row_constraints", "col_constraints"]:
            sim_settings[key] = bool(strtobool(str(sim_settings[key])))
        if sim_settings["row_constraints"]:
            sim_settings["scaling"] = "both" if sim_settings[
                "col_constraints"] else "const"
        else:
            sim_settings["scaling"] = "party" if sim_settings[
                "col_constraints"] else "total"
    for key in ["simulation_count", "gen_method", "scaling"]:
        if key not in sim_settings:
            raise KeyError(f"Missing data ('sim_settings.{key}')")
    sim_settings.setdefault("cpu_count", 4)
    sim_settings.setdefault("sens_cv", 0.01)
    sim_settings.setdefault("sens_method", "uniform")
    sim_settings.setdefault("sensitivity", False)
    sim_settings.setdefault("selected_rand_constit", "All constituencies")

    if "const_cov" not in sim_settings:
        sim_settings["const_cov"] = sim_settings["distribution_parameter"]
    if "party_vote_cov" not in sim_settings:
        sim_settings["party_vote_cov"] = sim_settings["const_cov"]/2
    if "use_thresholds" not in sim_settings:
        sim_settings["use_thresholds"] = False
    variance_coefficient = sim_settings["const_cov"]
    if sim_settings["gen_method"] == "beta":
        if variance_coefficient >= 0.75:
            raise ValueError("Coefficient of variation must be less than 0.75")
    elif sim_settings["gen_method"] == "uniform":
        if variance_coefficient >= 1/sqrt(3):
            raise ValueError("Coefficient of variation must be less than 0.57735")
    elif sim_settings["gen_method"] == "gamma":
        if variance_coefficient >= 1:
            raise ValueError("Coefficient of variation must be less than 1")
    if sim_settings["selected_rand_constit"] == "All":
        sim_settings["selected_rand_constit"] = "All constituencies"
    sim_count = sim_settings["simulation_count"]
    digoce = os.environ.get("FLASK_DIGITAL_OCEAN", "") == "True"
    if sim_count > 2000 and digoce:
        raise ValueError("Maximum iterations in the online version is 2000 (see Help)")
    return sim_settings
