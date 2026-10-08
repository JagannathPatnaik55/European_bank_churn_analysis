"""Association tests with sample sizes and effect sizes."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, mannwhitneyu


def _categorical_test(frame: pd.DataFrame, column: str) -> dict[str, Any]:
    table = pd.crosstab(frame[column], frame["Exited"])
    if table.shape[0] < 2 or table.shape[1] < 2:
        return {"variable": column, "test": "Chi-square independence", "n": int(len(frame)), "statistic": np.nan, "p_value": np.nan, "effect_size": np.nan, "null_hypothesis": f"{column} and churn are independent.", "interpretation": "Not estimable: fewer than two observed categories."}
    statistic, p_value, _, _ = chi2_contingency(table, correction=False)
    n = int(table.to_numpy().sum())
    denominator = min(table.shape[0] - 1, table.shape[1] - 1)
    effect = float(np.sqrt(statistic / (n * denominator))) if denominator and n else np.nan
    return {
        "variable": column,
        "test": "Chi-square independence",
        "n": n,
        "statistic": float(statistic),
        "p_value": float(p_value),
        "effect_size": effect,
        "null_hypothesis": f"{column} and churn are independent.",
        "interpretation": "Evidence of association; this observational comparison does not establish causation." if p_value < 0.05 else "No statistically significant association detected at the 5% level.",
    }


def _numeric_test(frame: pd.DataFrame, column: str) -> dict[str, Any]:
    retained = frame.loc[frame["Exited"] == 0, column].dropna()
    churned = frame.loc[frame["Exited"] == 1, column].dropna()
    result = {
        "variable": column,
        "test": "Mann–Whitney U (two-sided)",
        "n": int(len(retained) + len(churned)),
        "retained_n": int(len(retained)),
        "churned_n": int(len(churned)),
        "statistic": np.nan,
        "p_value": np.nan,
        "effect_size": np.nan,
        "null_hypothesis": f"The {column} distributions are equal for retained and churned customers.",
        "interpretation": "Not estimable: both outcome groups are required.",
    }
    if len(retained) and len(churned):
        test = mannwhitneyu(retained, churned, alternative="two-sided", method="auto")
        result["statistic"] = float(test.statistic)
        result["p_value"] = float(test.pvalue)
        result["effect_size"] = float(abs(test.statistic / (len(retained) * len(churned)) - 0.5) * 2)
        result["interpretation"] = "Evidence of a distributional difference; this observational comparison does not establish causation." if test.pvalue < 0.05 else "No statistically significant distributional difference detected at the 5% level."
    return result


def run_statistical_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    """Run pre-specified categorical and numeric churn association tests."""
    rows = [_categorical_test(frame, column) for column in ("Geography", "Gender", "IsActiveMember") if column in frame]
    rows.extend(_numeric_test(frame, column) for column in ("Age", "CreditScore", "Tenure", "Balance", "EstimatedSalary") if column in frame)
    results = pd.DataFrame(rows)
    results["p_value_adjusted"] = np.nan
    valid = results["p_value"].notna()
    p_values = results.loc[valid, "p_value"].to_numpy(dtype=float)
    if len(p_values):
        order = np.argsort(p_values)
        adjusted_sorted = np.maximum.accumulate(p_values[order] * (len(p_values) - np.arange(len(p_values)))).clip(0, 1)
        adjusted = np.empty_like(adjusted_sorted)
        adjusted[order] = adjusted_sorted
        results.loc[valid, "p_value_adjusted"] = adjusted
    results["significant"] = results["p_value_adjusted"] < 0.05
    results.loc[valid & results["significant"], "interpretation"] = (
        "Evidence of association after Holm correction; this observational comparison does not establish causation."
    )
    results.loc[valid & ~results["significant"], "interpretation"] = (
        "No statistically significant association detected after Holm correction at the 5% family-wise level."
    )
    return results
