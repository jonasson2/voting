"""File and reporting operations shared by the parallel simulation scripts."""

import json
import os
from pathlib import Path


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(value, file, indent=2, ensure_ascii=False)
        file.write("\n")
    os.replace(temporary, path)


def read_node_results(job_dir, manifest):
    """Read exactly the manifest's nodes and verify full replicate coverage."""
    from simulation_chunks import read_chunk_result

    nodes = manifest["nodes"]
    if not nodes or len({node["id"] for node in nodes}) != len(nodes):
        raise ValueError("Manifest must list distinct nodes")
    next_replicate = manifest["first_replicate"]
    results = []
    for node in nodes:
        if node["replicates"] <= 0 or node["start"] != next_replicate:
            raise ValueError("Manifest replicate ranges must be contiguous and non-overlapping")
        next_replicate += node["replicates"]
        result = read_chunk_result(Path(job_dir) / f"node-{node['id']:03d}.json")
        expected = (node["start"], next_replicate, node["replicates"], manifest["seed"])
        actual = (result["start_iteration"], result["next_global_iteration"],
                  result["iteration"], result["random_seed"])
        if actual != expected:
            raise ValueError(f"Node {node['id']} returned the wrong replicate range or seed")
        results.append(result)
    if next_replicate - manifest["first_replicate"] != manifest["replicates"]:
        raise ValueError("Manifest node ranges do not cover the requested replicates")
    return results


def write_reports(result, *, csv_path=None, excel_path=None, display_settings=None):
    if csv_path:
        from sim import write_csv
        write_csv(csv_path, result, display_settings)
        print(f"Report: {csv_path}", flush=True)
    if excel_path:
        from excel_util import simulation_to_xlsx
        simulation_to_xlsx(result.get_result_web(False), str(excel_path), display_settings)
        print(f"Excel: {excel_path}", flush=True)
