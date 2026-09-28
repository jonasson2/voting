#!/usr/bin/env python3
"""Run an offline simulation as independent local worker processes."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from math import ceil
from pathlib import Path
import secrets
import subprocess
import sys
from uuid import uuid4


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parsim.common import ROOT, create_job  # noqa: E402
from parsim.merge import merge_job  # noqa: E402
from offline import (  # noqa: E402
    UNSET, load_all_inputs, load_inputs, positive_int, seed_value,
)


def launch_worker(job_dir, chunk_id):
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("worker.py")),
         str(job_dir), str(chunk_id)],
        capture_output=True, text=True, check=False)
    return chunk_id, completed.returncode, completed.stderr.strip()


def run_job(votes, systems, settings, output, job_dir, chunk_size, workers):
    if settings["random_seed"] is None:
        settings["random_seed"] = secrets.randbelow(2**31)
    if chunk_size is None:
        chunk_size = max(1, ceil(settings["simulation_count"] / (4 * workers)))
    manifest = create_job(job_dir, votes, systems, settings, chunk_size)
    print(f"Job: {job_dir}", flush=True)
    print(f"Seed: {manifest['seed']}", flush=True)
    print(f"Chunks: {len(manifest['chunks'])}; local workers: {workers}",
          flush=True)

    failures = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(launch_worker, job_dir, chunk["id"])
                   for chunk in manifest["chunks"]]
        for future in as_completed(futures):
            chunk_id, code, error = future.result()
            if code:
                failures.append(chunk_id)
                print(f"Chunk {chunk_id} failed: {error}", file=sys.stderr)
    if failures:
        raise RuntimeError(
            f"{len(failures)} chunks failed; rerun them with worker.py, "
            f"then use merge.py on {job_dir}")
    merged = merge_job(job_dir, output)
    print(f"Report: {merged}")
    return merged


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-a", "--all", help="Download all file (JSON)")
    parser.add_argument("-v", "--votes", help="Vote table CSV")
    parser.add_argument("-e", "--systems",
                        help="Electoral system description (JSON)")
    parser.add_argument("-s", "--settings",
                        help="Simulation settings (JSON)")
    parser.add_argument("-o", "--output", required=True, help="Output CSV file")
    parser.add_argument("-r", "--replicates", type=positive_int,
                        help="Override the number of replicates")
    parser.add_argument("-C", "--cpus", type=positive_int,
                        help="Number of concurrent local workers")
    parser.add_argument("-S", "--seed", type=seed_value, default=UNSET,
                        help="Master random seed; - chooses one at random")
    parser.add_argument("--chunk-size", type=positive_int,
                        help="Replicates per chunk (default: about four per worker)")
    parser.add_argument("--job-dir", type=Path,
                        help="New job directory (default: parsim/jobs/<id>)")
    args = parser.parse_args(argv)
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
        workers = args.cpus or settings["cpu_count"]
        job_dir = args.job_dir or ROOT / "parsim" / "jobs" / uuid4().hex
        run_job(votes, systems, settings, args.output, job_dir,
                args.chunk_size, workers)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        parser.exit(1, f"run: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
