#!/usr/bin/env python3
"""Write CSV and Excel reports from an existing Elja simulation job."""

import argparse
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))


def report_job(job_dir, *, csv_path=None, excel_path=None):
    from input_files import validate_display_settings
    from parsim.common import read_node_results, write_reports
    from simulation_chunks import combine_chunks

    job_dir = Path(job_dir).expanduser().resolve()
    with (job_dir / "manifest.json").open(encoding="utf-8") as file:
        manifest = json.load(file)
    with (job_dir / "inputs.json").open(encoding="utf-8") as file:
        inputs = json.load(file)
    sources = {job_dir / "manifest.json", job_dir / "inputs.json"}
    sources.update(job_dir / f"node-{node['id']:03d}.json" for node in manifest["nodes"])
    if any(Path(path).expanduser().resolve() in sources
           for path in (csv_path, excel_path) if path):
        raise ValueError("Report outputs must not overwrite job inputs or node statistics")
    results = read_node_results(job_dir, manifest)
    display_settings = validate_display_settings(inputs["display_settings"])
    combined = combine_chunks(results)
    combined.input_files = manifest["input_files"]
    print(f"Job: {job_dir}", flush=True)
    print(f"Replicates: {combined.iteration}; seed: {manifest['seed']}", flush=True)
    write_reports(combined, csv_path=csv_path, excel_path=excel_path,
                  display_settings=display_settings)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=lambda prog: argparse.HelpFormatter(
            prog, max_help_position=44, width=110))
    parser.add_argument("job", help="Job ID under backend/parsim/jobs, or job directory")
    parser.add_argument("-o", "--csv", metavar="FILE", help="Output CSV file")
    parser.add_argument("-x", "--excel", metavar="FILE", help="Output Excel workbook (.xlsx)")
    args = parser.parse_args(argv)
    outputs = [Path(path).expanduser().resolve() for path in (args.csv, args.excel) if path]
    if not outputs:
        parser.error("provide -o/--csv and/or -x/--excel")
    if len(set(outputs)) != len(outputs):
        parser.error("CSV and Excel files must have different paths")
    job_dir = Path(args.job).expanduser()
    if not job_dir.is_dir() and job_dir.name == str(job_dir):
        job_dir = HERE / "jobs" / job_dir
    try:
        report_job(job_dir, csv_path=args.csv, excel_path=args.excel)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        parser.exit(1, f"elja-report: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
