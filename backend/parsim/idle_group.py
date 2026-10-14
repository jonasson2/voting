#!/usr/bin/env python3
"""Run one parsim worker per node in a multi-node idle allocation."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent


def run_group(job_dir, first_node_id, count):
    nodelist = os.environ.get("SLURM_JOB_NODELIST")
    if not nodelist:
        raise RuntimeError("Slurm did not provide a node list")
    result = subprocess.run(
        ["scontrol", "show", "hostnames", nodelist],
        check=True, capture_output=True, text=True)
    names = result.stdout.splitlines()
    if len(names) != count:
        raise RuntimeError(f"Expected {count} allocated nodes, got {len(names)}")
    workers = []
    for offset, name in enumerate(names):
        command = [
            sys.executable, str(HERE / "worker.py"),
            "--job-dir", str(job_dir),
            "--node-id", str(first_node_id + offset),
            "--node-name", name,
        ]
        workers.append((first_node_id + offset, subprocess.Popen(command)))
    while workers:
        for node_id, worker in workers[:]:
            code = worker.poll()
            if code is None:
                continue
            if code:
                print(f"idle_group: node {node_id} failed", file=sys.stderr)
                return code
            workers.remove((node_id, worker))
        if workers:
            time.sleep(0.2)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--first-node-id", type=int, required=True)
    parser.add_argument("--nodes", type=int, required=True)
    args = parser.parse_args(argv)
    if args.first_node_id < 0 or args.nodes < 1:
        parser.error("node IDs must be nonnegative and nodes must be positive")
    try:
        return run_group(args.job_dir, args.first_node_id, args.nodes)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"idle_group: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
