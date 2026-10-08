"""Regenerate static report figures from the configured raw dataset."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config, resolve_path
from src.data_loader import load_data
from src.preprocessing import create_segments
from src.visualizations import generate_figures


def main() -> None:
    config = load_config()
    raw = load_data(resolve_path(config, "raw_data"))
    segmentation = config.get("segmentation", {})
    tenure_groups = {name: tuple(bounds) for name, bounds in segmentation.get("tenure_groups", {"New": [0, 2], "Mid-term": [3, 6], "Long-term": [7, 10]}).items()}
    frame = create_segments(
        raw,
        credit_score_quantiles=tuple(segmentation.get("credit_score_quantiles", [1 / 3, 2 / 3])),
        high_value_quantile=float(segmentation.get("balance_high_value_quantile", 0.75)),
        age_upper_bounds=tuple(segmentation.get("age_upper_bounds", [29, 45, 60])),
        age_labels=list(segmentation.get("age_labels", ["<30", "30–45", "46–60", "60+"])),
        tenure_groups=tenure_groups,
    )
    paths = generate_figures(frame, resolve_path(config, "figure_dir"))
    print(f"Generated {len(paths)} figures in {resolve_path(config, 'figure_dir')}")


if __name__ == "__main__":
    main()
