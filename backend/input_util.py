from util import disp
from vote_table import check_vote_table

def parse_bool(value):
    value = value.lower()
    if value in {"y", "yes", "t", "true", "on", "1"}:
        return True
    if value in {"n", "no", "f", "false", "off", "0"}:
        return False
    raise ValueError(f"invalid truth value {value!r}")

def check_input(data, sections):
    for section in sections:
        if section not in data or not data[section]:
            print("raising error")
            raise KeyError(f"Missing data ('{section}')")
    return data

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
        ValueError: If relative SD is too high
    """
    if "row_constraints" in sim_settings and "col_constraints" in sim_settings:
        for key in ["row_constraints", "col_constraints"]:
            sim_settings[key] = parse_bool(str(sim_settings[key]))
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
    sim_settings.setdefault("sens_rsd", 0.01)
    sim_settings.setdefault("sens_method", "uniform")
    sim_settings.setdefault("sensitivity", False)
    if "const_cov" in sim_settings:
        sim_settings["const_rsd"] = sim_settings["const_cov"]
    if "party_vote_cov" in sim_settings:
        sim_settings["party_vote_rsd"] = sim_settings["party_vote_cov"]

    if "const_rsd" not in sim_settings:
        sim_settings["const_rsd"] = sim_settings["distribution_parameter"]
    if "const_corr" not in sim_settings:
        sim_settings["const_corr"] = 0
    if "party_vote_rsd" not in sim_settings:
        sim_settings["party_vote_rsd"] = sim_settings["const_rsd"]/2
    if "party_vote_corr" not in sim_settings:
        sim_settings["party_vote_corr"] = 0
    if "use_thresholds" not in sim_settings:
        sim_settings["use_thresholds"] = False
    variance_coefficient = sim_settings["const_rsd"]
    if sim_settings["gen_method"] == "beta":
        if variance_coefficient >= 0.75:
            raise ValueError("Relative standard deviation must be less than 0.75")
    elif sim_settings["gen_method"] == "uniform":
        if variance_coefficient >= 1/sqrt(3):
            raise ValueError("Relative standard deviation must be less than 0.57735")
    elif sim_settings["gen_method"] in ["gamma", "log-normal"]:
        if variance_coefficient >= 1:
            raise ValueError("Relative standard deviation must be less than 1")
    return sim_settings
