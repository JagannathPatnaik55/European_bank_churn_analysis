"""Convenience entry point for generating project artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pipeline import run_pipeline


if __name__ == "__main__":
    result = run_pipeline()
    print("Pipeline finished. Start the dashboard with: streamlit run dashboard/app.py")
    print(f"Observed churn: {result['kpis']['overall_churn_rate']:.1%}")
