#!/usr/bin/env python3
"""Run offline simulations from votes, electoral systems, and simulation settings."""

import argparse
import csv
from copy import deepcopy
from multiprocessing import Pool
from pathlib import Path

from input_files import (
    load_all, load_section, load_votes, prepare_simulation_inputs,
)
from simulation_chunks import (
    combine_chunks, run_chunk, split_replicates, write_chunk_result,
)


QUALITY_MEASURES = (
    ("sum_abs_party_overall", "Party-total absolute deviation"),
    ("sum_abs", "Constituency-list absolute deviation"),
    ("sum_sqshare", "Squared deviation per reference seat"),
    ("entropy_score", "Entropy score (%)"),
    ("geographical_displacement", "Geographical seat displacement"),
    ("constituency_disparity", "Constituency disparity"),
    ("max_overrepresentation", "Greatest relative over-representation (D'Hondt)"),
    ("total_overhang", "Potential overhang"),
)
SENSITIVITY_MEASURES = (
    ("sensitivity_between_parties", "Sensitivity: seats moving between parties"),
    ("sensitivity_within_parties", "Sensitivity: seats moving within parties"),
)
STATISTICS = (
    ("avg", "Mean"),
    ("std", "Standard deviation"),
    ("lo95", "95% CI lower"),
    ("hi95", "95% CI upper"),
)
DEFAULT_SENSITIVITY_COVS = (0.3, 1, 3)  # Percent, as in the web settings file.
UNSET = object()


class HelpParser(argparse.ArgumentParser):
    def format_help(self):
        help_text = super().format_help()
        return (help_text.replace("\x1b[1;32m", "\x1b[32m")
                         .replace("\x1b[1;33m", "\x1b[38;5;130m"))


def load_inputs(votes_path, systems_path, settings_path, overrides):
    if Path(votes_path).suffix != ".csv":
        raise ValueError("Vote input must be a CSV file in the standard vote format")
    votes = load_votes(votes_path)
    if isinstance(votes, str):
        raise ValueError(votes)
    systems = load_section(systems_path, "systems")
    settings = load_section(settings_path, "sim_settings")
    return prepare_inputs(votes, systems, settings, overrides)


def load_all_inputs(all_path, overrides):
    contents = load_all(all_path)
    return prepare_inputs(contents["vote_table"], contents["systems"],
                          contents["sim_settings"], overrides)


def prepare_inputs(votes, systems, settings, overrides):
    if not isinstance(settings, dict):
        raise ValueError("Simulation settings must be an object")
    settings = deepcopy(settings)
    for key, value in overrides.items():
        if value is not None or key == "random_seed":
            settings[key] = value
    settings["sensitivity"] = True
    settings["sensitivity_covs"] = list(DEFAULT_SENSITIVITY_COVS)
    votes, systems, settings = prepare_simulation_inputs(votes, systems, settings)
    names = [system["name"] for system in systems]
    if len(set(names)) != len(names):
        raise ValueError("Electoral system names must be unique for CSV columns")
    if type(settings["simulation_count"]) is not int or settings["simulation_count"] <= 0:
        raise ValueError("Number of simulations must be a positive integer")
    if type(settings["cpu_count"]) is not int or settings["cpu_count"] <= 0:
        raise ValueError("Number of CPUs must be a positive integer")
    return votes, systems, settings


def run_simulation(votes, systems, settings, first_replicate=0,
                   return_statistics=False):
    chunks = split_replicates(
        settings["simulation_count"], settings["cpu_count"], first_replicate)
    tasks = [(votes, systems, settings, count, start) for count, start in chunks]
    workers = len(tasks)
    if workers == 1:
        results = [run_chunk(*tasks[0])]
    else:
        with Pool(workers) as pool:
            results = pool.starmap(run_chunk, tasks)
    return combine_chunks(results, return_statistics=return_statistics)


def write_csv(path, result):
    names = [system["name"] for system in result.systems]
    with Path(path).open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Measure", "Statistic", *names])
        for measure, label in QUALITY_MEASURES:
            for statistic, statistic_label in STATISTICS:
                values = [
                    result.data[index][measure][statistic]
                    if (measure in result.data[index]
                        and (measure != "entropy_score"
                             or result.entropy_score_available[index])) else ""
                    for index in range(len(names))
                ]
                if measure == "entropy_score":
                    values = [value * 100 if value != "" else "" for value in values]
                writer.writerow([label, statistic_label, *values])
        if result.sensitivity:
            for measure, label in SENSITIVITY_MEASURES:
                for cov_index, cov in enumerate(result.sensitivity_data["covs"]):
                    row_label = f"{label} (CoV {cov:g}%)"
                    for statistic, statistic_label in STATISTICS:
                        values = result.sensitivity_data[measure][statistic][cov_index]
                        writer.writerow([row_label, statistic_label,
                                         *values[:len(names)]])


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def nonnegative_int(value):
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be a nonnegative integer")
    return number


def seed_value(value):
    return None if value == "-" else int(value)


def main(argv=None):
    parser = HelpParser(
        description=__doc__,
        usage="%(prog)s (-a ALL | -v VOTES -e SYSTEMS -s SETTINGS) "
              "[-o CSV] [-O STATFILE] [options]",
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog, max_help_position=36, width=80),
    )
    parser.add_argument("-a", "--all", help="Download all file (JSON)")
    parser.add_argument("-v", "--votes", help="Vote table CSV")
    parser.add_argument("-e", "--systems",
                        help="Electoral system description (JSON)")
    parser.add_argument("-s", "--settings",
                        help="Simulation settings (JSON)")
    parser.add_argument("-o", "--csv", help="Output CSV file")
    parser.add_argument("-O", "--output", metavar="STATFILE",
                        help="Output mergeable statistics (JSON)")
    parser.add_argument("-r", "--replicates", type=positive_int,
                        help="Override the number of replicates")
    parser.add_argument("-i", "--first-replicate", type=nonnegative_int, default=0,
                        help="First replicate number (zero-based; default: 0)")
    parser.add_argument("-C", "--cpus", type=positive_int,
                        help="Override the number of CPUs")
    parser.add_argument("-S", "--seed", type=seed_value, default=UNSET,
                        help="Random seed override; - chooses one at random")
    args = parser.parse_args(argv)
    if not args.csv and not args.output:
        parser.error("provide -o/--csv or -O/--output")
    if args.csv and args.output and Path(args.csv) == Path(args.output):
        parser.error("CSV and statistics files must have different paths")
    separate_inputs = (args.votes, args.systems, args.settings)
    if args.all:
        if any(separate_inputs):
            parser.error("-a/--all cannot be combined with -v, -e, or -s")
    elif not all(separate_inputs):
        parser.error("provide -a/--all or all of -v, -e, and -s")
    overrides = {
        "simulation_count": args.replicates,
        "cpu_count": args.cpus,
    }
    if args.seed is not UNSET:
        overrides["random_seed"] = args.seed
    try:
        if args.all:
            votes, systems, settings = load_all_inputs(args.all, overrides)
        else:
            votes, systems, settings = load_inputs(
                args.votes, args.systems, args.settings, overrides)
        if args.output:
            result, statistics = run_simulation(
                votes, systems, settings, first_replicate=args.first_replicate,
                return_statistics=True)
            write_chunk_result(args.output, statistics)
        else:
            result = run_simulation(
                votes, systems, settings, first_replicate=args.first_replicate)
        if args.csv:
            write_csv(args.csv, result)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
