#!/usr/bin/env python3
"""Run offline simulations from votes, electoral systems, and simulation settings."""

import argparse
import csv
from copy import deepcopy
from multiprocessing import Manager, Pool, TimeoutError
from pathlib import Path
import time

from input_files import (
    load_all, load_section, load_votes, prepare_simulation_inputs, validate_display_settings,
)
from simulation_report import simulation_settings, source_settings

from simulation_chunks import (
    combine_chunks, run_chunk, split_replicates, write_chunk_result,
)


UNSET = object()


class HelpParser(argparse.ArgumentParser):
    def format_help(self):
        help_text = super().format_help()
        return (help_text.replace("\x1b[1;32m", "\x1b[32m")
                         .replace("\x1b[1;33m", "\x1b[38;5;130m"))


def load_inputs(votes_path, systems_path, settings_path, overrides):
    """Return votes, systems, simulation settings, and default CSV precision."""
    if Path(votes_path).suffix != ".csv":
        raise ValueError("Vote input must be a CSV file in the standard vote format")
    votes = load_votes(votes_path)
    if isinstance(votes, str):
        raise ValueError(votes)
    systems = load_section(systems_path, "systems")
    settings = load_section(settings_path, "sim_settings")
    return (*prepare_inputs(votes, systems, settings, overrides), validate_display_settings())


def load_all_inputs(all_path, overrides):
    """Return the three simulation inputs and saved CSV precision."""
    contents = load_all(all_path)
    return (*prepare_inputs(contents["vote_table"], contents["systems"],
                            contents["sim_settings"], overrides),
            validate_display_settings(contents.get("display_settings")))


def prepare_inputs(votes, systems, settings, overrides):
    if not isinstance(settings, dict):
        raise ValueError("Simulation settings must be an object")
    settings = deepcopy(settings)
    for key, value in overrides.items():
        if value is not None or key == "random_seed":
            settings[key] = value
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
                   return_statistics=False, progress_path=None):
    chunks = split_replicates(
        settings["simulation_count"], settings["cpu_count"], first_replicate)
    tasks = [(votes, systems, settings, count, start) for count, start in chunks]
    workers = len(tasks)
    if progress_path is not None:
        from simulation_progress import INTERVAL, ReplicateMonitor, write_progress

        started = time.monotonic()
        total = settings["simulation_count"]
        with Manager() as manager:
            counts = manager.list([0] * workers)
            monitor = ReplicateMonitor(counts, [count for count, _ in chunks])
            write_progress(progress_path, counts, total, started)
            monitored_tasks = [(*task, index, monitor)
                               for index, task in enumerate(tasks)]
            with Pool(workers) as pool:
                pending = pool.starmap_async(run_chunk, monitored_tasks)
                while True:
                    try:
                        results = pending.get(timeout=INTERVAL)
                        break
                    except TimeoutError:
                        write_progress(progress_path, counts, total, started)
            write_progress(progress_path, counts, total, started)
    elif workers == 1:
        results = [run_chunk(*tasks[0])]
    else:
        with Pool(workers) as pool:
            results = pool.starmap(run_chunk, tasks)
    return combine_chunks(results, return_statistics=return_statistics)


def format_csv_entry(entry, display_settings):
    """Use the web entry's value, percentage flag, and confidence half-width."""
    if not isinstance(entry, dict):
        return entry
    scale = 100 if entry.get("percentage") else 1
    digits = (display_settings["percentage_digits"] if entry.get("percentage")
              else 0 if entry.get("integer") else display_settings["fractional_digits"])
    value = f"{scale * entry['value']:.{digits}f}"
    if entry["ci"] is None:
        return value + ("%" if entry.get("percentage") else "")
    interval = f"{value} ± {scale * entry['ci']:.{digits}f}"
    return f"({interval})%" if entry.get("percentage") else interval


def write_csv(path, result, display_settings=None):
    """Write the visible web table as comma-separated cells."""
    report = result.get_result_web(parallel=False)
    table = report["vuedata"]
    display_settings = validate_display_settings(display_settings)

    def columns(group):
        for stat in table["group_stats"].get(group, table["stats"]):
            yield stat, table["system_names"]

    with Path(path).open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Input files"])
        for label, filename in getattr(result, "input_files", {}).items():
            writer.writerow([label, filename])
        writer.writerow(["Source votes and seats"])
        writer.writerows(source_settings(report))
        writer.writerow(["Electoral systems", *table["system_names"]])
        writer.writerow(["Simulation settings"])
        writer.writerows((row["label"], row["data"])
                         for row in simulation_settings(report))
        writer.writerow(["First replicate number (zero-based)",
                         getattr(result, "start_iteration", 0)])
        writer.writerow([""])
        header = [table.get("initial_title", ""), ""]
        for stat, names in columns("shareTitle"):
            heading = "" if stat == "avg" else table["stat_headings"][stat]
            header.extend([heading, *[""] * (len(names) - 1)])
        writer.writerow(header)
        writer.writerow(["", "", *[name for _, names in columns("shareTitle")
                                for name in names]])
        for group in table["group_ids"]:
            if group == "shareTitle" or not table["show"][group]:
                continue
            option = table["group_options"].get(group)
            if option and not table["display_options"].get(option):
                continue
            side_title = table["side_titles"].get(group)
            title = table["group_titles"][group].replace("\n", " ")
            heading_type = table["headingType"].get(group)
            if table.get("block_headers", {}).get(group):
                names = [name for _, names in columns(group) for name in names]
                writer.writerow([table["block_headers"][group], "", *names])
            if not side_title and (title or heading_type == "systems"):
                names = [name for _, names in columns(group) for name in names]
                writer.writerow([title, "", *names] if heading_type == "systems"
                                else [title])
            rows = [] if group in table["group_messages"] else table[group]
            for row in rows:
                if row.get("option") and not table["display_options"].get(row["option"]):
                    continue
                writer.writerow([title if side_title else "", row["rowtitle"], *[
                    format_csv_entry(entry, display_settings)
                    for stat, _ in columns(group) for entry in row[stat]]])
                title = ""
            if group in table["group_messages"]:
                writer.writerow([title, table["group_messages"][group]])
            if group in table["footnotes"]:
                writer.writerow([table["footnotes"][group]])


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


def input_file_names(args):
    """Record the original command-line inputs, rather than node staging files."""
    if args.all:
        return {"Download all file": str(args.all)}
    return {"Votes file": str(args.votes), "Electoral systems file": str(args.systems),
            "Simulation settings file": str(args.settings)}


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
    parser.add_argument("--progress", metavar="FILE", type=Path,
                        help="Write periodic replicate progress (JSON)")
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
    if args.progress and any(args.progress.resolve() == Path(path).resolve()
                             for path in (args.csv, args.output) if path):
        parser.error("Progress and result files must have different paths")
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
            votes, systems, settings, display_settings = load_all_inputs(args.all, overrides)
        else:
            votes, systems, settings, display_settings = load_inputs(
                args.votes, args.systems, args.settings, overrides)
        if args.output:
            result, statistics = run_simulation(
                votes, systems, settings, first_replicate=args.first_replicate,
                return_statistics=True, progress_path=args.progress)
            statistics["input_files"] = input_file_names(args)
            write_chunk_result(args.output, statistics)
        else:
            result = run_simulation(
                votes, systems, settings, first_replicate=args.first_replicate,
                progress_path=args.progress)
        result.input_files = input_file_names(args)
        if args.csv:
            write_csv(args.csv, result, display_settings)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
