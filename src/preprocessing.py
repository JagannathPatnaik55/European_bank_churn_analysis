"""Business-friendly, reproducible customer segmentation."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


AGE_LABELS = ["<30", "30–45", "46–60", "60+"]
TENURE_LABELS = ["New", "Mid-term", "Long-term"]


def segment_age(
    values: Iterable[float],
    upper_bounds: tuple[int, int, int] = (29, 45, 60),
    labels: list[str] | None = None,
) -> pd.Series:
    """Assign disjoint age groups; the final band starts above the third bound."""
    series = pd.Series(values)
    categories = labels or AGE_LABELS
    return pd.cut(series, bins=[-np.inf, *upper_bounds, np.inf], labels=categories, right=True, ordered=True)


def assign_tenure_group(
    values: Iterable[float], groups: dict[str, tuple[int, int]] | None = None
) -> pd.Series:
    """Group tenure as New (0–2), Mid-term (3–6), or Long-term (7–10)."""
    series = pd.Series(values)
    configured_groups = groups or {"New": (0, 2), "Mid-term": (3, 6), "Long-term": (7, 10)}
    labels = list(configured_groups)
    upper_bounds = [configured_groups[label][1] for label in labels]
    return pd.cut(series, bins=[-np.inf, *upper_bounds], labels=labels, right=True, ordered=True)


def assign_credit_score_segment(
    values: Iterable[float], quantiles: tuple[float, float] = (1 / 3, 2 / 3)
) -> tuple[pd.Series, dict[str, float]]:
    """Create Low/Medium/High score groups using sample tertile cutoffs."""
    series = pd.Series(values, dtype="float64")
    valid = series.dropna()
    if valid.empty:
        result = pd.Series(pd.Categorical([None] * len(series), categories=["Low", "Medium", "High"], ordered=True), index=series.index)
        return result, {"low_cutoff": float("nan"), "high_cutoff": float("nan")}
    low, high = (float(valid.quantile(q)) for q in quantiles)
    if low < high:
        labels = np.select([series <= low, series <= high], ["Low", "Medium"], default="High")
    else:
        ranked = series.rank(method="average", pct=True)
        labels = np.select([ranked <= quantiles[0], ranked <= quantiles[1]], ["Low", "Medium"], default="High")
    labels = pd.Series(labels, index=series.index, dtype="object").where(series.notna(), None)
    result = pd.Series(pd.Categorical(labels, categories=["Low", "Medium", "High"], ordered=True), index=series.index)
    return result, {"low_cutoff": low, "high_cutoff": high}


def assign_balance_segment(values: Iterable[float]) -> pd.Series:
    """Separate zero balances from low/high positive balances at their median."""
    series = pd.Series(values, dtype="float64")
    positive = series[series > 0]
    cutoff = float(positive.median()) if not positive.empty else float("nan")
    result = pd.Series(index=series.index, dtype="object")
    result.loc[series == 0] = "Zero-balance"
    result.loc[(series > 0) & (series <= cutoff)] = "Low-balance"
    result.loc[series > cutoff] = "High-balance"
    result.loc[series.isna()] = None
    return pd.Series(
        pd.Categorical(result, categories=["Zero-balance", "Low-balance", "High-balance"], ordered=True),
        index=series.index,
    )


def assign_high_value_flag(
    values: Iterable[float], quantile: float = 0.75
) -> tuple[pd.Series, float | None]:
    """Flag customers at or above a positive-balance percentile threshold."""
    series = pd.Series(values, dtype="float64")
    positive = series[series > 0]
    if positive.empty:
        return pd.Series(False, index=series.index, dtype=bool), None
    threshold = float(positive.quantile(quantile))
    return (series >= threshold).fillna(False).astype(bool), threshold


def create_segments(
    frame: pd.DataFrame,
    *,
    credit_score_quantiles: tuple[float, float] = (1 / 3, 2 / 3),
    high_value_quantile: float = 0.75,
    age_upper_bounds: tuple[int, int, int] = (29, 45, 60),
    age_labels: list[str] | None = None,
    tenure_groups: dict[str, tuple[int, int]] | None = None,
) -> pd.DataFrame:
    """Return an analytical copy with derived segments and no surname field."""
    result = frame.drop(columns=["Surname"], errors="ignore").copy()
    result["AgeSegment"] = segment_age(result["Age"], age_upper_bounds, age_labels)
    result["CreditScoreSegment"], _ = assign_credit_score_segment(result["CreditScore"], credit_score_quantiles)
    result["TenureGroup"] = assign_tenure_group(result["Tenure"], tenure_groups)
    result["BalanceSegment"] = assign_balance_segment(result["Balance"])
    high_value, _ = assign_high_value_flag(result["Balance"], high_value_quantile)
    result["HighValueCustomer"] = high_value
    result["ActivityLabel"] = result["IsActiveMember"].map({0: "Inactive", 1: "Active"})
    result["CreditCardLabel"] = result["HasCrCard"].map({0: "No credit card", 1: "Credit card holder"})
    return result


def restore_segment_categories(
    frame: pd.DataFrame, age_labels: list[str] | None = None
) -> pd.DataFrame:
    """Restore ordered segment dtypes after reading the processed CSV."""
    result = frame.copy()
    categories = {
        "AgeSegment": age_labels or AGE_LABELS,
        "CreditScoreSegment": ["Low", "Medium", "High"],
        "TenureGroup": TENURE_LABELS,
        "BalanceSegment": ["Zero-balance", "Low-balance", "High-balance"],
    }
    for column, labels in categories.items():
        if column in result.columns:
            result[column] = pd.Categorical(result[column], categories=labels, ordered=True)
    return result
