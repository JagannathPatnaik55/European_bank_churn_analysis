"""End-to-end data pipeline for outputs, figures, and stakeholder reports."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.analytics import financial_profile_analysis, geography_age_analysis, summarize_all_segments
from src.config import load_config, resolve_path
from src.data_loader import load_data
from src.data_validation import validate_data
from src.high_value_analysis import high_value_summary
from src.insights import generate_insights
from src.kpis import calculate_overall_kpis, engagement_churn_indicator
from src.preprocessing import assign_credit_score_segment, assign_high_value_flag, create_segments
from src.reporting import generate_report_bundle
from src.statistical_analysis import run_statistical_analysis
from src.visualizations import generate_figures


LOGGER = logging.getLogger("churn_analysis")


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def run_pipeline(
    *,
    raw_data_path: str | Path | None = None,
    processed_data_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    figure_dir: str | Path | None = None,
    report_dir: str | Path | None = None,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load, validate, prepare, analyze, plot, and report from a raw CSV."""
    config = load_config(config_path)
    raw_path = Path(raw_data_path) if raw_data_path else resolve_path(config, "raw_data")
    processed_path = Path(processed_data_path) if processed_data_path else resolve_path(config, "processed_data")
    outputs = Path(output_dir) if output_dir else resolve_path(config, "output_dir")
    figures = Path(figure_dir) if figure_dir else resolve_path(config, "figure_dir")
    reports = Path(report_dir) if report_dir else resolve_path(config, "report_dir")
    for directory in (processed_path.parent, outputs, figures, reports):
        directory.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Loading raw customer file")
    raw = load_data(raw_path)
    validation = validate_data(raw)
    for issue in validation.issues:
        log_method = LOGGER.error if issue.severity == "error" else LOGGER.warning if issue.severity == "warning" else LOGGER.info
        log_method("%s (%s): %s", issue.code, issue.count, issue.message)

    segmentation = config.get("segmentation", {})
    credit_quantiles = tuple(segmentation.get("credit_score_quantiles", [1 / 3, 2 / 3]))
    high_value_quantile = float(segmentation.get("balance_high_value_quantile", 0.75))
    age_upper_bounds = tuple(int(value) for value in segmentation.get("age_upper_bounds", [29, 45, 60]))
    age_labels = list(segmentation.get("age_labels", ["<30", "30–45", "46–60", "60+"]))
    tenure_groups = {name: tuple(int(value) for value in bounds) for name, bounds in segmentation.get("tenure_groups", {"New": [0, 2], "Mid-term": [3, 6], "Long-term": [7, 10]}).items()}
    prepared = create_segments(
        raw,
        credit_score_quantiles=(float(credit_quantiles[0]), float(credit_quantiles[1])),
        high_value_quantile=high_value_quantile,
        age_upper_bounds=age_upper_bounds,
        age_labels=age_labels,
        tenure_groups=tenure_groups,
    )
    _write_csv(prepared, processed_path)

    kpis = calculate_overall_kpis(prepared, config.get("project", {}).get("target_column", "Exited"))
    segment_summaries = summarize_all_segments(prepared)
    combined = pd.concat(
        [table.assign(dimension=dimension) for dimension, table in segment_summaries.items()], ignore_index=True
    ) if segment_summaries else pd.DataFrame()
    _write_csv(combined, outputs / "segment_summary.csv")
    for dimension, table in segment_summaries.items():
        file_name = {
            "AgeSegment": "age_analysis.csv",
            "CreditScoreSegment": "credit_score_analysis.csv",
            "TenureGroup": "tenure_analysis.csv",
            "BalanceSegment": "balance_analysis.csv",
            "IsActiveMember": "engagement_analysis.csv",
            "HasCrCard": "credit_card_analysis.csv",
            "NumOfProducts": "product_analysis.csv",
        }.get(dimension, f"{dimension.lower()}_analysis.csv")
        output_table = table.copy()
        if dimension == "Geography":
            output_table["geographic_risk_index"] = output_table["churn_index"]
        _write_csv(output_table, outputs / file_name)

    high_value = high_value_summary(prepared)
    _write_csv(high_value, outputs / "high_value_analysis.csv")
    _write_csv(geography_age_analysis(prepared), outputs / "geography_age_analysis.csv")
    _write_csv(financial_profile_analysis(prepared), outputs / "financial_profile_analysis.csv")
    _write_csv(pd.DataFrame([kpis]), outputs / "overall_kpis.csv")
    _write_csv(pd.DataFrame([engagement_churn_indicator(prepared)]), outputs / "engagement_kpis.csv")
    _write_csv(pd.DataFrame([{
        "churned_balance_exposure": kpis["churned_balance_exposure"],
        "churned_balance_share": kpis["churned_balance_share"],
        "churner_average_balance": kpis["churner_average_balance"],
        "churner_median_balance": kpis["churner_median_balance"],
        "high_value_churn_balance_exposure": kpis["high_value_churn_balance_exposure"],
    }]), outputs / "financial_exposure.csv")

    credit_thresholds = assign_credit_score_segment(raw["CreditScore"], (float(credit_quantiles[0]), float(credit_quantiles[1])))[1]
    _, balance_threshold = assign_high_value_flag(raw["Balance"], high_value_quantile)
    positive_balance_median = float(raw.loc[raw["Balance"] > 0, "Balance"].median()) if (raw["Balance"] > 0).any() else None
    age_labels_by_range = {
        age_labels[0]: f"18–{age_upper_bounds[0]}",
        age_labels[1]: f"{age_upper_bounds[0] + 1}–{age_upper_bounds[1]}",
        age_labels[2]: f"{age_upper_bounds[1] + 1}–{age_upper_bounds[2]}",
        age_labels[3]: f"{age_upper_bounds[2] + 1}+",
    }
    definitions = {
        "age": age_labels_by_range,
        "credit_score": {"method": "sample tertiles", **credit_thresholds},
        "tenure": {name: f"{bounds[0]}–{bounds[1]} years" for name, bounds in tenure_groups.items()},
        "balance": {"Zero-balance": "Balance exactly equals zero", "Low-balance": "Positive balance up to positive-balance median", "High-balance": "Positive balance above positive-balance median", "positive_balance_median": positive_balance_median},
        "high_value_customer": {"method": f"positive balance >= {high_value_quantile:.0%} quantile", "balance_threshold": balance_threshold, "interpretation": "high-balance proxy, not customer profitability"},
        "year": "snapshot provenance; constant in source file; excluded from explanatory analysis",
    }
    (outputs / "segmentation_definitions.json").write_text(json.dumps(definitions, indent=2), encoding="utf-8")

    statistics = run_statistical_analysis(prepared)
    insights = generate_insights(
        prepared,
        minimum_segment_size=int(segmentation.get("minimum_insight_segment_size", 100)),
        minimum_rate_difference=float(segmentation.get("minimum_insight_rate_difference", 0.05)),
    )
    _write_csv(statistics, outputs / "statistical_tests.csv")
    _write_csv(insights, outputs / "key_insights.csv")
    _write_csv(pd.DataFrame([validation.to_dict()]), outputs / "data_quality_summary.csv")

    LOGGER.info("Generating static figures")
    figure_paths = generate_figures(prepared, figures)
    report_paths = generate_report_bundle(reports, prepared, kpis, validation, segment_summaries, high_value, statistics, insights, definitions)
    LOGGER.info("Pipeline complete: %s rows, %s churned", kpis["total_customers"], kpis["churned_customers"])
    return {
        "raw_data_path": raw_path,
        "processed_data_path": processed_path,
        "output_dir": outputs,
        "figure_paths": figure_paths,
        "report_paths": report_paths,
        "validation": validation,
        "kpis": kpis,
        "segment_summaries": segment_summaries,
        "high_value": high_value,
        "statistics": statistics,
        "insights": insights,
    }
