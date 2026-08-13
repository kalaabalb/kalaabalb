#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.pipeline import write_foundation_assets


def main() -> int:
    write_foundation_assets()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
