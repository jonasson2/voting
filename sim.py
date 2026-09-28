#!/usr/bin/env python3
"""Command-line entry point for offline election simulations."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from offline import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
