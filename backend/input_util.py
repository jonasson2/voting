import os
from distutils.util import strtobool
from dictionaries import SEAT_SPECIFICATION_OPTIONS
from copy import deepcopy
from util import disp
def check_input(data, sections):
    for section in sections:
        if section not in data or not data[section]:
            print("raising error")
            raise KeyError(f"Missing data ('{section}')")
    return data

def check_vote_table(vote_table):
    """Checks vote_table input, and translates empty cells to zeroes

    Raises:
        KeyError: If vote_table or constituencies are missing a component
        ValueError: If the dimensions of the table are inconsistent,
            negative values are supplied as vote counts,
            some constituency has no votes or seats specified,
            or constituency names are not unique
        TypeError: If vote or seat counts are not given as numbers
    """
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
            notok = row[p] >= 1 and type(row[p]) != int
            # if row[p] >= 1 and type(row[p]) != int:
            #     raise TypeError("Votes must be whole numbers.")
            if row[p]<0:
                raise ValueError("Votes may not be negative.")
        if sum(row)==0:
            raise ValueError("Every constituency needs some votes.")

    for const in table["constituencies"]:
        if "name" not in const: # or not const["name"]:
            raise KeyError(f"Missing data ('vote_table.constituencies[x].name')")
        name = const["name"]
        for info in ["num_const_seats", "num_adj_seats"]:
            if info not in const:
                raise KeyError(f"Missing data ('{info}' for {name})")
            if not const[info]: const[info] = 0
            if type(const[info]) != int:
                raise TypeError("Seat specifications must be numbers.")
        if const["num_const_seats"]+const["num_adj_seats"] <= 0:
            raise ValueError("Constituency seats and adjustment seats "
                             "must add to a nonzero number. "
                             f"This is not the case for {name}.")

    seen = set()
    for const in table["constituencies"]:
        if False: #const["name"] in seen:
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
        # option = electoral_system["seat_spec_option"]
        # assert option in SEAT_SPECIFICATION_OPTIONS.keys(), (
        #     f"Unexpected seat specification option encountered: {option}.")
        # if option == "custom":
        # We only really need to check input if option is "custom",
        # because in case of the other options this won't be evaluated anyway,
        # except for option "one_const", and even then,
        # the frontend can't reach a state where that option would be corrupted.
        # But let's just check all, to be helpful also
        # in case POST data does not come from frontend but elsewhere.
        for const in electoral_system["constituencies"]:
            if "name" not in const: # or not const["name"]:
                #can never happen in case of input from frontend
                raise KeyError(f"Missing data ('constituencies[x].name' in "
                    f"electoral system {electoral_system['name']})")
            name = const["name"]
            for info in ["num_const_seats", "num_adj_seats"]:
                if info not in const:
                    raise KeyError(f"Missing data ('{info}' for {name} in "
                        f"electoral system {electoral_system['name']})")
                if not const[info]: const[info]=0
                if type(const[info]) != int:
                    raise TypeError("Seat specifications must be numbers.")
            if (const["num_const_seats"] + const["num_adj_seats"] <= 0):
                raise ValueError("Constituency seats and adjustment seats "
                     "must add to a nonzero number. "
                     f"This is not the case for {name} in "
                     f"electoral system {electoral_system['name']}.")
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
            sim_settings["scaling"] = "both" if sim_settings["col_constraints"] else "const"
        else:
            sim_settings["scaling"] = "party" if sim_settings["col_constraints"] else "total"
    for key in ["simulation_count", "gen_method", "scaling"]:
        if key not in sim_settings:
            raise KeyError(f"Missing data ('sim_settings.{key}')")
    if "distribution_parameter" not in sim_settings:
        raise KeyError("Missing data ('sim_settings.distribution_parameter')")
    variance_coefficient = sim_settings["distribution_parameter"]
    if sim_settings["gen_method"] == "beta":
        if variance_coefficient >= 0.75:
            raise ValueError("Coefficient of variation must be less than 0.75")
    elif sim_settings["gen_method"] == "uniform":
        if variance_coefficient >= 1/sqrt(3):
            raise ValueError("Coefficient of variation must be less than 0.57735")
    elif sim_settings["gen_method"] == "gamma":
        if variance_coefficient >= 1:
            raise ValueError("Coefficient of variation must be less than 1")
    if "sens_cv" not in sim_settings:
        sim_settings["sens_cv"] = 0.01
    if "sensitivity" not in sim_settings:
        sensitivity = False
    sim_count = sim_settings["simulation_count"]
    digoce = os.environ.get("FLASK_DIGITAL_OCEAN", "") == "True"
    if sim_count > 2000 and digoce:
        raise ValueError("Maximum iterations in the online version is 2000 (see Help)")
    return sim_settings
