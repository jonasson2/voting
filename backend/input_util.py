import math

from dictionaries import (
    ADJUSTMENT_METHODS,
    DIVIDER_RULES,
    REGIONAL_ADJUSTMENT_METHODS,
    SPECIAL_RULE_NAMES,
)


def normalize_system(system):
    """Add defaults for settings saved before newer system fields existed."""
    legacy_eligibility = system.pop("fixed_seat_eligibility", None)
    if legacy_eligibility not in (None, "constituency", "national-or-constituency"):
        raise ValueError(f"Unknown fixed-seat eligibility rule: {legacy_eligibility}")
    system.setdefault(
        "fixed_seat_threshold_choice",
        1 if legacy_eligibility != "constituency" else 0,
    )
    if "fixed_seat_national_threshold" not in system:
        system["fixed_seat_national_threshold"] = (
            system.get("adjustment_threshold", 0)
            if legacy_eligibility == "national-or-constituency" else 0)
    system.setdefault("require_votes_in_all_constituencies", False)
    system.setdefault("special_rules", "none")
    system.setdefault("regional_adjustment_method", "max-const-votes")
    system.setdefault("regional_adjustment_divider", "sainte-lague")
    system.setdefault("compare_with", True)
    return system

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
            raise KeyError(f"Missing data ('{section}')")
    return data

def check_system_names(electoral_systems):
    for system in electoral_systems:
        name = system.get("name") if isinstance(system, dict) else None
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Electoral system names cannot be blank.")
    return electoral_systems

def check_systems(electoral_systems):
    """Checks election systems constituency input, and translates empty cells to 0

    Raises:
        KeyError: If constituencies are missing a component
        TypeError: If seat counts are not given as numbers
        ValueError: If not enough seats are specified
    """
    if not electoral_systems:
        raise ValueError("Must have at least one electoral system.")
    check_system_names(electoral_systems)
    electoral_systems = [e for e in electoral_systems if e["name"] != "Monge"]
    # Monge is iffy and thus removed
    for electoral_system in electoral_systems:
        normalize_system(electoral_system)
        national_threshold = electoral_system["fixed_seat_national_threshold"]
        if electoral_system["fixed_seat_threshold_choice"] not in (0, 1) or isinstance(
                electoral_system["fixed_seat_threshold_choice"], bool):
            raise ValueError("Fixed-seat threshold combination must be And or Or.")
        if (isinstance(national_threshold, bool)
                or not isinstance(national_threshold, (int, float))
                or not math.isfinite(national_threshold)
                or not 0 <= national_threshold <= 100):
            raise ValueError(
                "National threshold for fixed seats must be a number between 0 and 100%; blank is not allowed.")
        adjustment_threshold = electoral_system["adjustment_threshold"]
        if (isinstance(adjustment_threshold, bool)
                or not isinstance(adjustment_threshold, (int, float))
                or not math.isfinite(adjustment_threshold)
                or not 0 <= adjustment_threshold <= 100):
            raise ValueError(
                "National threshold for adjustment seats must be a number between 0 and 100%; blank is not allowed.")
        if not isinstance(electoral_system["require_votes_in_all_constituencies"], bool):
            raise ValueError("Standing in all constituencies must be Yes or No.")
        special_rules = electoral_system["special_rules"]
        if special_rules not in {
                item["value"] for item in SPECIAL_RULE_NAMES}:
            raise ValueError(f"Unknown special rules: {special_rules}")
        regional_method = electoral_system["regional_adjustment_method"]
        if regional_method not in REGIONAL_ADJUSTMENT_METHODS:
            raise ValueError(
                f"Unknown regional adjustment-seat method: {regional_method}")
        regional_divider = electoral_system["regional_adjustment_divider"]
        if regional_divider not in DIVIDER_RULES:
            raise ValueError(
                f"Unknown regional adjustment-seat rule: {regional_divider}")
        adjustment_method = electoral_system["adjustment_method"]
        if adjustment_method not in ADJUSTMENT_METHODS:
            raise ValueError(
                f"Unknown adjustment-seat method: {adjustment_method}")
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
    sim_settings.setdefault("sensitivity", False)
    sim_settings.setdefault("sensitivity_simulation_count", 3)
    sim_settings.setdefault("sensitivity_gen_method", "uniform")
    sim_settings.setdefault("sensitivity_covs", [1, 2, 3])
    seed = sim_settings.get("random_seed")
    if seed in (None, "", "-"):
        sim_settings["random_seed"] = None
    elif type(seed) is not int or not -(2**31) <= seed < 2**31:
        raise ValueError(
            "Random seed must be an integer from -2147483648 to 2147483647.")
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
    entropy_score = sim_settings.get("entropy_score", True)
    if not isinstance(entropy_score, bool):
        entropy_score = parse_bool(str(entropy_score))
    sim_settings["entropy_score"] = entropy_score
    sensitivity = sim_settings.get("sensitivity", False)
    if not isinstance(sensitivity, bool):
        sensitivity = parse_bool(str(sensitivity))
    sim_settings["sensitivity"] = sensitivity
    if sensitivity:
        sensitivity_count = sim_settings["sensitivity_simulation_count"]
        if (type(sensitivity_count) is not int or sensitivity_count <= 0):
            raise ValueError(
                "Number of sensitivity simulations must be a positive integer.")
        generating_methods = {"beta", "gamma", "log-normal", "uniform"}
        if sim_settings["sensitivity_gen_method"] not in generating_methods:
            raise ValueError("Unknown sensitivity generating distribution.")
        from sensitivity import sensitivity_covs
        covs = sensitivity_covs(sim_settings["sensitivity_covs"])
        sim_settings["sensitivity_covs"] = [100 * cov for cov in covs]
        maximum_sensitivity_cov = covs[-1]
        sensitivity_method = sim_settings["sensitivity_gen_method"]
        if sensitivity_method == "beta" and maximum_sensitivity_cov >= 0.75:
            raise ValueError(
                "Maximum sensitivity CoV must be less than 75% for beta draws.")
        if (sensitivity_method == "uniform"
                and maximum_sensitivity_cov >= 1 / sqrt(3)):
            raise ValueError(
                "Maximum sensitivity CoV must be less than 57.735% for uniform draws.")
        if (sensitivity_method in {"gamma", "log-normal"}
                and maximum_sensitivity_cov >= 1):
            raise ValueError(
                "Maximum sensitivity CoV must be less than 100% for this distribution.")
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
