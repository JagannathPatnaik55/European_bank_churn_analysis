"""Regenerate the complete analytical report bundle from source data."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_pipeline


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    result = run_pipeline()
    print("Reports regenerated from the raw data and current configuration:")
    for path in result["report_paths"].values():
        print(f"- {path}")


if __name__ == "__main__":
    main()
