#!/usr/bin/env python3
"""Validate and merge a parallel simulation job into one CSV report."""

import argparse
import os
from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parsim.common import chunk_path, load_job  # noqa: E402
from offline import write_csv  # noqa: E402
from simulation_chunks import combine_chunks, read_chunk_record  # noqa: E402


def merge_job(job_dir, output):
    job_dir = Path(job_dir)
    manifest, inputs = load_job(job_dir)
    expected_paths = {
        chunk_path(job_dir, chunk["id"]) for chunk in manifest["chunks"]}
    actual_paths = set(job_dir.glob("chunk-*.json"))
    missing = expected_paths - actual_paths
    extra = actual_paths - expected_paths
    if missing or extra:
        raise ValueError(
            f"Chunk files do not match the manifest: "
            f"{len(missing)} missing, {len(extra)} unexpected")

    results = []
    expected_names = [system["name"] for system in inputs["systems"]]
    for chunk in manifest["chunks"]:
        record = read_chunk_record(chunk_path(job_dir, chunk["id"]))
        metadata = record.get("metadata")
        expected_metadata = {
            "job_id": manifest["job_id"],
            "job_sha256": manifest["job_sha256"],
            "input_sha256": manifest["input_sha256"],
            "chunk_id": chunk["id"],
            "start": chunk["start"],
            "count": chunk["count"],
        }
        result = record["result"]
        if metadata != expected_metadata:
            raise ValueError(f"Chunk {chunk['id']} belongs to another job or range")
        if (result.get("iteration") != chunk["count"]
                or result.get("sim_count") != chunk["count"]
                or result.get("start_iteration") != chunk["start"]
                or result.get("random_seed") != manifest["seed"]
                or [system["name"] for system in result.get("systems", [])]
                    != expected_names):
            raise ValueError(f"Chunk {chunk['id']} has inconsistent results")
        results.append(result)

    combined = combine_chunks(results)
    if combined.iteration != manifest["replicates"]:
        raise ValueError("Merged replicate count does not match the job")
    output = Path(output)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
    os.close(fd)
    try:
        write_csv(temporary, combined)
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job_dir", help="Job directory created by run.py")
    parser.add_argument("-o", "--output", required=True, help="Output CSV file")
    args = parser.parse_args(argv)
    try:
        output = merge_job(args.job_dir, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"merge: {error}\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
