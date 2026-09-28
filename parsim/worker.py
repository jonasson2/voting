#!/usr/bin/env python3
"""Run one numbered chunk from a parallel simulation job."""

import argparse
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parsim.common import chunk_path, load_job  # noqa: E402
from simulation_chunks import run_chunk, write_chunk_result  # noqa: E402


def run_worker(job_dir, chunk_id):
    manifest, inputs = load_job(job_dir)
    if not 0 <= chunk_id < len(manifest["chunks"]):
        raise ValueError(f"Unknown chunk number: {chunk_id}")
    chunk = manifest["chunks"][chunk_id]
    result = run_chunk(
        inputs["votes"], inputs["systems"], inputs["settings"],
        chunk["count"], chunk["start"])
    if result["iteration"] != chunk["count"]:
        raise RuntimeError(f"Chunk {chunk_id} stopped before completion")
    metadata = {
        "job_id": manifest["job_id"],
        "job_sha256": manifest["job_sha256"],
        "input_sha256": manifest["input_sha256"],
        "chunk_id": chunk_id,
        "start": chunk["start"],
        "count": chunk["count"],
    }
    path = chunk_path(job_dir, chunk_id)
    write_chunk_result(path, result, metadata)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job_dir", help="Job directory created by run.py")
    parser.add_argument("chunk_id", type=int, help="Chunk number from manifest.json")
    args = parser.parse_args(argv)
    try:
        path = run_worker(args.job_dir, args.chunk_id)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        parser.exit(1, f"worker: {error}\n")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
