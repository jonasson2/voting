"""File readers and input checks shared by web and offline simulations."""

import csv
import json
import os
from io import StringIO
from pathlib import Path

from electionHandler import update_constituencies
from input_util import check_simul_settings, check_system_names, normalize_system
from util import load_votes_from_excel, remove_blank_rows
from vote_table import check_vote_table, process_vote_table


OBSOLETE_SYSTEM_KEYS = {
    "regional_adjustment_rule", "seat_spec_option",
    "fixed_seat_eligibility", "constituency_allocation_rule",
    "adjustment_division_rule", "adjustment_allocation_rule",
}
OBSOLETE_SIMULATION_KEYS = {
    "row_constraints", "col_constraints", "distribution_parameter",
}
SIMULATION_KEY_ALIASES = {
    "const_cov": "const_rsd", "party_vote_cov": "party_vote_rsd",
}


def read_json(source):
    if isinstance(source, (Path, str)):
        with open(os.path.expanduser(source), encoding="utf-8") as file:
            return json.load(file)
    return json.load(source.stream if hasattr(source, "stream") else source)


def load_section(source, key):
    contents = read_json(source)
    if not isinstance(contents, dict) or set(contents) != {key}:
        raise ValueError(f"Expected a {key}-only JSON file from Download")
    return contents[key]


def validate_systems(systems):
    if not isinstance(systems, list):
        raise ValueError("Electoral systems must be a list.")
    for system in systems:
        if not isinstance(system, dict):
            raise ValueError("Each electoral system must be an object.")
        obsolete = OBSOLETE_SYSTEM_KEYS & system.keys()
        if obsolete:
            raise ValueError(f"Obsolete electoral-system field: {sorted(obsolete)[0]}")
        normalize_system(system)
    check_system_names(systems)
    return systems


def validate_settings(settings):
    if not isinstance(settings, dict):
        raise ValueError("Simulation settings must be an object.")
    # Older downloads can retain stale aliases alongside the current values.
    # Use an alias only when its replacement is absent, then discard it.
    for old, current in SIMULATION_KEY_ALIASES.items():
        if old in settings:
            settings.setdefault(current, settings.pop(old))
    obsolete = OBSOLETE_SIMULATION_KEYS & settings.keys()
    if obsolete:
        raise ValueError(f"Obsolete simulation setting: {sorted(obsolete)[0]}")
    return check_simul_settings(settings)


def load_systems(source):
    return validate_systems(load_section(source, "systems"))


def load_settings(source):
    return validate_settings(load_section(source, "sim_settings"))


def validate_display_settings(settings=None):
    """Read saved precision only; older offline inputs use 3 and 1 digits."""
    if settings is None:
        settings = {}
    if not isinstance(settings, dict):
        raise ValueError("Display settings must be an object.")
    digits = {}
    for key, default in (("fractional_digits", 3), ("percentage_digits", 1)):
        value = settings.get(key, default)
        if type(value) is not int or not 0 <= value <= 10:
            raise ValueError(f"{key} must be an integer between 0 and 10")
        digits[key] = value
    return digits


def load_json(source):
    """Read a systems-and-settings file, optionally including votes."""
    contents = read_json(source)
    if not isinstance(contents, dict):
        raise ValueError("Expected a JSON object containing systems and settings")
    if "e_settings" in contents:
        raise ValueError("Obsolete settings field: e_settings")
    if "systems" not in contents or "sim_settings" not in contents:
        raise ValueError("Expected systems and sim_settings in JSON file")
    contents["systems"] = validate_systems(contents["systems"])
    contents["sim_settings"] = validate_settings(contents["sim_settings"])
    if "vote_table" in contents:
        contents["vote_table"] = check_vote_table(contents["vote_table"])
    if "display_settings" in contents:
        contents["display_settings"] = validate_display_settings(contents["display_settings"])
    return contents


def load_all(source):
    contents = load_json(source)
    if set(contents) - {"display_settings"} != {"vote_table", "systems", "sim_settings"}:
        raise ValueError("Expected a Download all file with votes, systems, and settings")
    return contents


def load_votes(filename, stream=None):
    if str(filename).endswith(".csv"):
        if stream:
            text = stream.read().decode("utf-8-sig")
            rows = list(csv.reader(StringIO(text), skipinitialspace=True))
        else:
            with open(filename, "r", encoding="utf-8-sig", newline="") as file:
                rows = list(csv.reader(file, skipinitialspace=True))
    elif str(filename).endswith("xlsx"):
        rows = load_votes_from_excel(stream, filename)
    else:
        return "Neither .csv nor .xlsx file"
    rows = remove_blank_rows(rows)
    vote_table = process_vote_table(rows, filename)
    return (check_vote_table(vote_table)
            if not isinstance(vote_table, str) else vote_table)


def prepare_simulation_inputs(votes, systems, settings):
    """Validate in-memory inputs before starting a simulation."""
    votes = check_vote_table(votes)
    systems = validate_systems(systems)
    settings = validate_settings(settings)
    constituencies, national_seats = update_constituencies(votes, systems)
    for system, seats, national in zip(systems, constituencies, national_seats):
        system["constituencies"] = seats
        system["nat_seats"] = national
    return votes, systems, settings
