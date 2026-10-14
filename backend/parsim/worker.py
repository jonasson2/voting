#!/usr/bin/env python3
"""Run one node's assigned sim.py replicate range."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def run_allocated(job_dir, node_id):
    from parsim.common import atomic_json

    job_dir = Path(job_dir)
    atomic_json(job_dir / f"allocation-{node_id:03d}.json", {
        "node_id": node_id,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    })
    assignment = job_dir / f"assignment-{node_id:03d}.json"
    deadline = time.monotonic() + 600
    while not assignment.exists():
        if (job_dir / "stop").exists():
            return 1
        if time.monotonic() >= deadline:
            raise RuntimeError("Master did not assign work within 10 minutes")
        time.sleep(0.2)
    with assignment.open(encoding="utf-8") as file:
        work = json.load(file)
    command = [
        sys.executable, str(BACKEND / "sim.py"),
        "-a", str(job_dir / "inputs.json"),
        "-r", str(work["replicates"]), "-i", str(work["start"]),
        "-C", str(work["cores"]), "-S", str(work["seed"]),
        "-O", str(job_dir / f"node-{node_id:03d}.json"),
        "--progress", str(job_dir / f"progress-{node_id:03d}.json"),
    ]
    command = ["srun", "--nodes=1", "--ntasks=1",
               f"--cpus-per-task={work['slurm_cpus']}", "--exact", *command]
    return subprocess.run(command, check=False).returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--node-id", type=int, required=True)
    args = parser.parse_args(argv)
    if args.node_id < 0:
        parser.error("node ID must be nonnegative")
    try:
        return run_allocated(args.job_dir, args.node_id)
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        parser.exit(1, f"worker: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
