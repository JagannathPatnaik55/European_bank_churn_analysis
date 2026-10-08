"""Command-line entry point for the complete analytics pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the European bank churn analysis pipeline.")
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config.yaml", help="YAML configuration path")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    result = run_pipeline(config_path=args.config)
    print(
        f"Completed: {result['kpis']['total_customers']:,} customers, "
        f"{result['kpis']['churned_customers']:,} churned "
        f"({result['kpis']['overall_churn_rate']:.1%})."
    )
    print(f"Reports: {result['report_paths']['research_paper'].parent}")
    print(f"Outputs: {result['output_dir']}")


if __name__ == "__main__":
    main()
