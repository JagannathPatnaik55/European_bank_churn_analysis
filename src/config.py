"""Central configuration loading and path resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Read YAML configuration and resolve configured paths from project root."""
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    config["_config_path"] = config_path.resolve()
    config["_project_root"] = PROJECT_ROOT
    return config


def resolve_path(config: dict[str, Any], key: str) -> Path:
    """Resolve one configured path relative to the project root."""
    raw_path = Path(config["paths"][key])
    return raw_path if raw_path.is_absolute() else Path(config["_project_root"]) / raw_path
