"""Job files shared by the local master, worker, and merger."""

import hashlib
import json
from pathlib import Path
import sys
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

JOB_FORMAT_VERSION = 1


def digest(value):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def source_digest():
    """Fingerprint the Python code used to run and merge a job."""
    paths = sorted(
        path for base in (ROOT / "backend", ROOT / "parsim")
        for path in base.rglob("*.py")
        if "tests" not in path.relative_to(base).parts)
    hasher = hashlib.sha256()
    for path in paths:
        hasher.update(str(path.relative_to(ROOT)).encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


def chunk_path(job_dir, chunk_id):
    return Path(job_dir) / f"chunk-{chunk_id:06d}.json"


def _read_json(path):
    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


def _write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write("\n")


def make_chunks(replicates, chunk_size):
    return [
        {"id": index, "start": start,
         "count": min(chunk_size, replicates - start)}
        for index, start in enumerate(range(0, replicates, chunk_size))
    ]


def create_job(job_dir, votes, systems, settings, chunk_size):
    job_dir = Path(job_dir)
    job_dir.mkdir(parents=True, exist_ok=False)
    inputs = {"votes": votes, "systems": systems, "settings": settings}
    manifest = {
        "format_version": JOB_FORMAT_VERSION,
        "job_id": uuid4().hex,
        "input_sha256": digest(inputs),
        "source_sha256": source_digest(),
        "replicates": settings["simulation_count"],
        "seed": settings["random_seed"],
        "chunks": make_chunks(settings["simulation_count"], chunk_size),
    }
    manifest["job_sha256"] = digest(manifest)
    _write_json(job_dir / "inputs.json", inputs)
    _write_json(job_dir / "manifest.json", manifest)
    return manifest


def load_job(job_dir):
    job_dir = Path(job_dir)
    manifest = _read_json(job_dir / "manifest.json")
    inputs = _read_json(job_dir / "inputs.json")
    if not isinstance(manifest, dict) or not isinstance(inputs, dict):
        raise ValueError("Invalid job files")
    job_hash = manifest.get("job_sha256")
    unsigned = {key: value for key, value in manifest.items()
                if key != "job_sha256"}
    if (manifest.get("format_version") != JOB_FORMAT_VERSION
            or not isinstance(manifest.get("job_id"), str)
            or not isinstance(job_hash, str)
            or digest(unsigned) != job_hash
            or digest(inputs) != manifest.get("input_sha256")):
        raise ValueError("Job manifest or input snapshot does not match its hash")
    if source_digest() != manifest.get("source_sha256"):
        raise ValueError("Python source has changed since this job was created")
    count = manifest.get("replicates")
    chunks = manifest.get("chunks")
    if (type(count) is not int or count <= 0
            or type(manifest.get("seed")) is not int
            or not isinstance(chunks, list) or not chunks):
        raise ValueError("Invalid job replicate ranges or seed")
    next_start = 0
    for index, chunk in enumerate(chunks):
        if (not isinstance(chunk, dict) or chunk.get("id") != index
                or type(chunk.get("start")) is not int
                or type(chunk.get("count")) is not int
                or chunk["start"] != next_start or chunk["count"] <= 0):
            raise ValueError("Job chunks contain a gap, overlap, or duplicate")
        next_start += chunk["count"]
    if next_start != count:
        raise ValueError("Job chunks do not cover all replicates")
    if (set(inputs) != {"votes", "systems", "settings"}
            or inputs["settings"].get("random_seed") != manifest["seed"]
            or inputs["settings"].get("simulation_count") != count):
        raise ValueError("Job inputs do not match the manifest")
    return manifest, inputs
