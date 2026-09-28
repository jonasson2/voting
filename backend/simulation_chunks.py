"""Run and combine independent ranges of simulation replicates."""

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile

import numpy as np

from simulate import Sim_result, Simulation


CHUNK_FORMAT_VERSION = 1


def _json_value(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Cannot save {type(value).__name__} in a chunk result")


def write_chunk_result(path, result, metadata=None):
    """Atomically save a run_chunk result, including mergeable statistics."""
    path = Path(path)
    payload = {"format_version": CHUNK_FORMAT_VERSION, "result": result}
    if metadata is not None:
        payload["metadata"] = metadata
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(payload, file, default=_json_value, allow_nan=False,
                      ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_chunk_record(path):
    """Load a chunk result and its optional job metadata."""
    with Path(path).open(encoding="utf-8") as file:
        payload = json.load(file)
    if (not isinstance(payload, dict)
            or payload.get("format_version") != CHUNK_FORMAT_VERSION
            or not isinstance(payload.get("result"), dict)
            or not isinstance(payload["result"].get("stat"), dict)):
        raise ValueError("Unrecognized simulation chunk result format")
    return payload


def read_chunk_result(path):
    """Load statistics in the form accepted by combine_chunks."""
    return read_chunk_record(path)["result"]


def split_replicates(count, workers):
    if count <= 0 or workers <= 0:
        raise ValueError("Replicates and workers must be positive")
    workers = min(count, workers)
    start = 0
    chunks = []
    for index in range(workers):
        size = count // workers + (index < count % workers)
        chunks.append((size, start))
        start += size
    return chunks


def run_chunk(votes, systems, settings, count, start_iteration, nr=0,
              monitor=None):
    worker_settings = deepcopy(settings)
    worker_settings["simulation_count"] = count
    simulation = Simulation(worker_settings, deepcopy(systems), deepcopy(votes),
                            nr=nr, start_iteration=start_iteration)
    simulation.simulate(nr, monitor)
    return simulation.attributes()


def combine_chunks(results):
    combined = Sim_result(results[0])
    for result in results[1:]:
        combined.combine(Sim_result(result))
    combined.analysis()
    return combined
