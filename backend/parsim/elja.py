#!/usr/bin/env python3
"""Run one offline simulation across several nodes, using sim.py on each node."""

import argparse
import csv
import json
from math import floor, isfinite
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import time
from uuid import uuid4

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))


def read_partitions(path):
    with Path(path).open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter="\t")
        if reader.fieldnames != ["Nodes", "Cores", "MaxNode", "Speed", "Part"]:
            raise ValueError("Invalid partitions.txt header")
        records = list(reader)
    if not records:
        raise ValueError("Partition list is empty")
    names = set()
    rows = []
    for record in records:
        name = record["Part"]
        if not name or name in names:
            raise ValueError("Partition names must be nonempty and unique")
        names.add(name)
        total_nodes = int(record["Nodes"])
        cores_per_node = int(record["Cores"])
        max_nodes = total_nodes if record["MaxNode"] == "INF" else int(record["MaxNode"])
        speed_per_core = float(record["Speed"])
        if total_nodes <= 0 or cores_per_node <= 0 or max_nodes <= 0:
            raise ValueError(f"{name}: node and core counts must be positive")
        if not isfinite(speed_per_core) or speed_per_core <= 0:
            raise ValueError(f"{name}: Speed must be positive")
        rows.append({"partition": name, "total_nodes": total_nodes,
                     "cores_per_node": cores_per_node, "max_nodes": max_nodes,
                     "speed_per_core": speed_per_core})
    return rows


def split_counts(replicates, nodes):
    """Give each node work, then weight the rest by cores times speed per core."""
    if replicates < len(nodes):
        raise ValueError("Replicates must be at least the number of nodes")
    weights = [node["cores"] * node["speed_per_core"] for node in nodes]
    remaining = replicates - len(nodes)
    exact = [remaining * weight / sum(weights) for weight in weights]
    counts = [1 + floor(value) for value in exact]
    surplus = replicates - sum(counts)
    order = sorted(range(len(nodes)), key=lambda index:
                   (exact[index] - floor(exact[index]), -index), reverse=True)
    for index in order[:surplus]:
        counts[index] += 1
    return counts


def build_assignments(replicates, nodes, first_replicate=0):
    start = first_replicate
    for node, count in zip(nodes, split_counts(replicates, nodes)):
        node["start"] = start
        node["replicates"] = count
        start += count
    return nodes


def stop_launchers(launchers, job_dir):
    (Path(job_dir) / "stop").touch(exist_ok=True)
    for process in launchers:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    for process in launchers:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()


def wait_ready(path, process, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            with path.open(encoding="utf-8") as file:
                return json.load(file)
        if process.poll() is not None:
            return None
        time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for allocation {path.name}")


def launch_node(job_dir, node_id, partition, slurm_cpus, immediate, log):
    child = [sys.executable, str(HERE / "worker.py"),
             "--job-dir", str(job_dir), "--node-id", str(node_id)]
    command = [
        "salloc", f"--immediate={immediate}", "--exclusive", "--mem=0",
        f"--partition={partition}", "--nodes=1", "--ntasks=1",
        f"--cpus-per-task={slurm_cpus}", f"--job-name=parsim-{node_id:03d}",
        *child,
    ]
    return subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                            start_new_session=True)


def available_node_count(partition, slurm_cpus):
    """Count fully idle nodes that can satisfy our exclusive CPU request."""
    try:
        result = subprocess.run(
            ["sinfo", "-N", "-h", f"--partition={partition}",
             "-o", "%N|%t|%c"],
            check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError(f"Cannot query Slurm availability for {partition}: "
                           f"{error}") from error
    nodes = set()
    for line in result.stdout.splitlines():
        fields = line.strip().split("|")
        if len(fields) != 3:
            raise ValueError(f"Unexpected sinfo row: {line}")
        name, state, cpus = fields
        if state == "idle" and int(cpus) >= slurm_cpus:
            nodes.add(name)
    return len(nodes)


def wait_for_nodes(active, nodes, job_dir):
    from simulation_progress import INTERVAL, ProgressDisplay

    started = time.monotonic()
    display = ProgressDisplay()
    finished = set()
    width = 0
    next_update = started
    terminal = sys.stdout.isatty()
    try:
        while True:
            for node_id, process, log_name in active:
                code = process.poll()
                if code is not None:
                    if code:
                        raise RuntimeError(f"Node {node_id} failed; inspect {log_name}")
                    finished.add(node_id)
            now = time.monotonic()
            done = len(finished) == len(active)
            if now >= next_update or done:
                snapshots = {}
                for node in nodes:
                    path = job_dir / f"progress-{node['id']:03d}.json"
                    try:
                        with path.open(encoding="utf-8") as file:
                            snapshots[node['id']] = json.load(file)
                    except FileNotFoundError:
                        pass
                line = display.line(nodes, snapshots, finished, now - started)
                print(("\r" + line.ljust(width)) if terminal else line,
                      end="" if terminal else "\n", flush=True)
                width = max(width, len(line))
                next_update = now + INTERVAL
            if done:
                break
            time.sleep(0.2)
    finally:
        if terminal:
            print(flush=True)


def run_distributed(votes, systems, settings, *, csv_path, stat_path, job_dir,
                    partitions, target_nodes, first_replicate, core_cap, immediate,
                    display_settings=None):
    from parsim.common import atomic_json
    from sim import write_csv
    from input_files import validate_display_settings
    from simulation_chunks import combine_chunks, read_chunk_result, write_chunk_result

    if settings["random_seed"] is None:
        settings["random_seed"] = secrets.randbelow(2**31)
    if settings["simulation_count"] < target_nodes:
        raise ValueError("Replicates must be at least the requested node count")
    job_dir = Path(job_dir).resolve()
    job_dir.mkdir(parents=True, exist_ok=False)
    display_settings = validate_display_settings(display_settings)
    atomic_json(job_dir / "inputs.json", {
        "vote_table": votes, "systems": systems, "sim_settings": settings,
        "display_settings": display_settings,
    })
    launchers = []
    active = []
    logs = []
    nodes = []
    try:
        for partition in partitions:
            pending = []
            cores = partition["cores_per_node"]
            if core_cap:
                cores = min(cores, core_cap)
            slurm_cpus = 2 * partition["cores_per_node"]
            available = available_node_count(partition["partition"], slurm_cpus)
            if not available:
                print(f"{partition['partition']}: no eligible idle nodes", flush=True)
                continue
            # Request the remaining nodes together, so allocation waits overlap.
            for _ in range(min(available, partition["total_nodes"],
                               target_nodes - len(nodes))):
                node_id = len(launchers)
                log = (job_dir / f"attempt-{node_id:03d}.log").open("x")
                logs.append(log)
                process = launch_node(job_dir, node_id, partition["partition"],
                                      slurm_cpus, immediate, log)
                launchers.append(process)
                pending.append((node_id, process, log.name))
            for node_id, process, log_name in pending:
                ready = wait_ready(job_dir / f"allocation-{node_id:03d}.json",
                                   process, immediate + 30)
                if ready is None:
                    process.wait()
                    print(f"{partition['partition']}: no immediate allocation",
                          flush=True)
                    continue
                if ready["node_id"] != node_id:
                    raise RuntimeError("Allocation reported an unexpected node ID")
                nodes.append({
                    "id": node_id, "partition": partition["partition"],
                    "cores": cores, "slurm_cpus": slurm_cpus,
                    "speed_per_core": partition["speed_per_core"],
                    "slurm_job_id": ready["slurm_job_id"],
                })
                active.append((node_id, process, log_name))
                print(f"{partition['partition']}: started node "
                      f"{len(nodes)}/{target_nodes}", flush=True)
            if len(nodes) == target_nodes:
                break
        if len(nodes) != target_nodes:
            raise RuntimeError(f"Started {len(nodes)} of {target_nodes} requested "
                               "nodes; all listed partitions were tried")

        build_assignments(settings["simulation_count"], nodes, first_replicate)
        atomic_json(job_dir / "manifest.json", {
            "job_id": job_dir.name, "seed": settings["random_seed"],
            "replicates": settings["simulation_count"],
            "first_replicate": first_replicate, "nodes": nodes,
        })
        print(f"Job: {job_dir}", flush=True)
        print(f"Seed: {settings['random_seed']}", flush=True)
        for node in nodes:
            atomic_json(job_dir / f"assignment-{node['id']:03d}.json", {
                "start": node["start"], "replicates": node["replicates"],
                "cores": node["cores"], "slurm_cpus": node["slurm_cpus"],
                "seed": settings["random_seed"],
            })
        wait_for_nodes(active, nodes, job_dir)
        print("Combining node results...", flush=True)

        results = []
        for node in nodes:
            result = read_chunk_result(job_dir / f"node-{node['id']:03d}.json")
            expected = (node["start"], node["start"] + node["replicates"],
                        node["replicates"], settings["random_seed"])
            actual = (result["start_iteration"],
                      result["next_global_iteration"], result["iteration"],
                      result["random_seed"])
            if actual != expected:
                raise ValueError(f"Node {node['id']} returned the wrong "
                                 "replicate range or seed")
            results.append(result)
        if stat_path:
            combined, statistics = combine_chunks(results, return_statistics=True)
            write_chunk_result(stat_path, statistics)
        else:
            combined = combine_chunks(results)
        if csv_path:
            write_csv(csv_path, combined, display_settings)
            print(f"Report: {csv_path}", flush=True)
        if stat_path:
            print(f"Statistics: {stat_path}", flush=True)
    finally:
        stop_launchers(launchers, job_dir)
        for log in logs:
            log.close()


def main(argv=None):
    from sim import (UNSET, load_all_inputs, load_inputs, nonnegative_int,
                     positive_int, seed_value)

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog, max_help_position=44, width=110),
    )
    parser.add_argument("-n", "--nodes", type=positive_int, required=True,
                        help="Number of nodes to start")
    parser.add_argument("-a", "--all", help="Download all file (JSON)")
    parser.add_argument("-v", "--votes", help="Vote table CSV")
    parser.add_argument("-e", "--systems",
                        help="Electoral system description (JSON)")
    parser.add_argument("-s", "--settings", help="Simulation settings (JSON)")
    parser.add_argument("-o", "--csv", help="Output CSV file")
    parser.add_argument("-O", "--output", metavar="STATFILE",
                        help="Output mergeable statistics (JSON)")
    parser.add_argument("-r", "--replicates", type=positive_int,
                        help="Override the number of replicates")
    parser.add_argument("-i", "--first-replicate", type=nonnegative_int,
                        default=0, help="First replicate number (zero-based)")
    parser.add_argument("-C", "--cores", type=positive_int,
                        help="Maximum simulation processes per node")
    parser.add_argument("-S", "--seed", type=seed_value, default=UNSET,
                        help="Master random seed; - chooses one at random")
    parser.add_argument("--job-dir", type=Path,
                        help="New job directory (default: backend/parsim/jobs/<id>)")
    parser.add_argument("--partitions", type=Path, default=HERE / "partitions.txt",
                        help="Ordered tab-separated partition list")
    parser.add_argument("--immediate", type=positive_int, default=5,
                        help="Seconds allowed for each Slurm allocation")
    args = parser.parse_args(argv)
    if not args.csv and not args.output:
        parser.error("provide -o/--csv or -O/--output")
    if args.csv and args.output and Path(args.csv) == Path(args.output):
        parser.error("CSV and statistics files must have different paths")
    if args.all:
        if any((args.votes, args.systems, args.settings)):
            parser.error("-a cannot be combined with -v, -e, or -s")
    elif not all((args.votes, args.systems, args.settings)):
        parser.error("provide -a or all of -v, -e, and -s")
    overrides = {"simulation_count": args.replicates}
    if args.seed is not UNSET:
        overrides["random_seed"] = args.seed
    try:
        votes, systems, settings, display_settings = (
            load_all_inputs(args.all, overrides) if args.all else
            load_inputs(args.votes, args.systems, args.settings, overrides))
        partitions = read_partitions(args.partitions)
        run_distributed(
            votes, systems, settings, csv_path=args.csv, stat_path=args.output,
            job_dir=args.job_dir or HERE / "jobs" / uuid4().hex,
            partitions=partitions, target_nodes=args.nodes,
            first_replicate=args.first_replicate, core_cap=args.cores,
            immediate=args.immediate, display_settings=display_settings)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        parser.exit(1, f"elja: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
