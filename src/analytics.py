"""Reusable grouped churn and financial-profile analysis."""

from __future__ import annotations

import pandas as pd

from src.kpis import calculate_churn_rate


SEGMENT_DIMENSIONS = {
    "Geography": "Geography",
    "AgeSegment": "AgeSegment",
    "CreditScoreSegment": "CreditScoreSegment",
    "TenureGroup": "TenureGroup",
    "BalanceSegment": "BalanceSegment",
    "Gender": "Gender",
    "IsActiveMember": "IsActiveMember",
    "HasCrCard": "HasCrCard",
    "NumOfProducts": "NumOfProducts",
}


def summarize_segments(
    frame: pd.DataFrame, segment_column: str, target_column: str = "Exited"
) -> pd.DataFrame:
    """Summarize segment size, churn rate, contribution, and risk index."""
    if segment_column not in frame.columns:
        raise KeyError(f"Segment column not found: {segment_column}")
    if target_column not in frame.columns:
        raise KeyError(f"Target column not found: {target_column}")
    overall_rate = calculate_churn_rate(frame[target_column])
    total_churn = int((frame[target_column] == 1).sum())
    grouped = frame.groupby(segment_column, observed=True, dropna=False)[target_column].agg(
        customer_count="size", churned_count="sum"
    )
    grouped["retained_count"] = grouped["customer_count"] - grouped["churned_count"]
    grouped["churn_rate"] = grouped["churned_count"] / grouped["customer_count"].replace(0, pd.NA)
    grouped["churn_contribution"] = grouped["churned_count"] / total_churn if total_churn else 0.0
    grouped["overall_churn_rate"] = overall_rate
    grouped["churn_index"] = grouped["churn_rate"] / overall_rate if overall_rate and overall_rate > 0 else float("nan")
    grouped["overrepresented_among_churners"] = grouped["churn_contribution"] > (
        grouped["customer_count"] / len(frame) if len(frame) else 0
    )
    grouped.index.name = "segment"
    summary = grouped.reset_index()
    summary["segment"] = summary["segment"].astype("string").fillna("Missing")
    if segment_column == "IsActiveMember":
        summary["segment"] = summary["segment"].map({"0": "Inactive", "1": "Active"}).fillna(summary["segment"])
    elif segment_column == "HasCrCard":
        summary["segment"] = summary["segment"].map({"0": "No credit card", "1": "Credit card holder"}).fillna(summary["segment"])
    return summary


def summarize_all_segments(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create a summary table for each required churn dimension."""
    return {
        dimension: summarize_segments(frame, column)
        for dimension, column in SEGMENT_DIMENSIONS.items()
        if column in frame.columns
    }


def geography_age_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    """Return churn counts/rates for each observed geography-age pair."""
    return frame.groupby(["Geography", "AgeSegment"], observed=True).agg(
        customer_count=("Exited", "size"), churned_count=("Exited", "sum"), churn_rate=("Exited", "mean")
    ).reset_index()


def financial_profile_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    """Compare selected numeric profiles for retained and churned customers."""
    numeric = [column for column in ("Age", "CreditScore", "Tenure", "Balance", "EstimatedSalary", "NumOfProducts") if column in frame]
    if not numeric:
        return pd.DataFrame()
    grouped = frame.groupby("Exited", observed=True)[numeric].agg(["count", "mean", "median"])
    grouped.columns = [f"{column}_{stat}" for column, stat in grouped.columns]
    grouped.index.name = "Exited"
    return grouped.reset_index()
