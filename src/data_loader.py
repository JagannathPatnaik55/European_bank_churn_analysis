"""CSV ingestion with actionable file and schema errors."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_validation import validate_schema


def load_data(path: str | Path) -> pd.DataFrame:
    """Load the supplied CSV without modifying it and validate its schema."""
    data_path = Path(path)
    if not data_path.exists():
        expected = "data/raw/European_Bank.csv" if data_path.name == "European_Bank.csv" else str(data_path)
        raise FileNotFoundError(f"Dataset not found. Please place European_Bank.csv in {expected}.")
    try:
        frame = pd.read_csv(data_path, encoding="utf-8-sig")
    except (UnicodeDecodeError, pd.errors.ParserError) as exc:
        raise ValueError(f"Could not read dataset at {data_path}: {exc}") from exc
    validate_schema(frame)
    return frame
