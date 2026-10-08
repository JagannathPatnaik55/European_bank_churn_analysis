"""Central KPI calculations used by reports and the dashboard."""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

import pandas as pd


def calculate_churn_rate(exited: Iterable[Any]) -> float:
    """Return churn as a proportion in [0, 1], or NaN for an empty population."""
    values = pd.Series(exited).dropna()
    if values.empty:
        return math.nan
    return float((values == 1).sum() / len(values))


def calculate_overall_kpis(frame: pd.DataFrame, target_column: str = "Exited") -> dict[str, float | int]:
    """Calculate population, churn, and balance-exposure KPIs for a frame."""
    total = int(len(frame))
    churned = frame.loc[frame[target_column] == 1]
    retained = frame.loc[frame[target_column] == 0]
    total_balance = float(frame["Balance"].sum()) if "Balance" in frame else float("nan")
    churned_balance = float(churned["Balance"].sum()) if "Balance" in frame else float("nan")
    churn_balance = churned["Balance"] if "Balance" in frame else pd.Series(dtype=float)
    high_value = frame[frame["HighValueCustomer"]] if "HighValueCustomer" in frame else frame.iloc[0:0]
    high_value_churn = high_value[high_value[target_column] == 1]
    return {
        "total_customers": total,
        "retained_customers": int(len(retained)),
        "churned_customers": int(len(churned)),
        "overall_churn_rate": calculate_churn_rate(frame[target_column]),
        "average_balance": float(frame["Balance"].mean()) if total and "Balance" in frame else float("nan"),
        "churned_balance_exposure": churned_balance,
        "churned_balance_share": churned_balance / total_balance if total_balance else 0.0,
        "churner_average_balance": float(churn_balance.mean()) if len(churn_balance) else float("nan"),
        "churner_median_balance": float(churn_balance.median()) if len(churn_balance) else float("nan"),
        "high_value_customer_count": int(len(high_value)),
        "high_value_churned_count": int(len(high_value_churn)),
        "high_value_churn_rate": calculate_churn_rate(high_value[target_column]) if len(high_value) else float("nan"),
        "high_value_churn_ratio": float(len(high_value_churn) / len(churned)) if len(churned) else 0.0,
        "high_value_churn_balance_exposure": float(high_value_churn["Balance"].sum()) if "Balance" in frame else 0.0,
    }


def geographic_risk_index(frame: pd.DataFrame, geography_column: str = "Geography") -> dict[str, float]:
    """Compute country churn rate divided by the filtered portfolio rate."""
    overall = calculate_churn_rate(frame["Exited"])
    if math.isnan(overall) or overall == 0:
        return {str(country): math.nan for country in frame[geography_column].dropna().unique()}
    rates = frame.groupby(geography_column, observed=True)["Exited"].mean()
    return {str(country): float(rate / overall) for country, rate in rates.items()}


def engagement_churn_indicator(frame: pd.DataFrame) -> dict[str, float | int]:
    """Compare inactive and active churn rates without implying causality."""
    inactive = frame.loc[frame["IsActiveMember"] == 0, "Exited"]
    active = frame.loc[frame["IsActiveMember"] == 1, "Exited"]
    inactive_rate = calculate_churn_rate(inactive)
    active_rate = calculate_churn_rate(active)
    return {
        "inactive_count": int(len(inactive)),
        "active_count": int(len(active)),
        "inactive_churn_rate": inactive_rate,
        "active_churn_rate": active_rate,
        "rate_difference": inactive_rate - active_rate if not math.isnan(inactive_rate) and not math.isnan(active_rate) else math.nan,
    }
