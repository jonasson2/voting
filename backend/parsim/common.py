"""File operations shared by the parallel simulation master and workers."""

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
