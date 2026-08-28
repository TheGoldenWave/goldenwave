#!/usr/bin/env python3
"""GoldenWave experimental Candidate Contract entrypoint."""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from gw_candidate.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
