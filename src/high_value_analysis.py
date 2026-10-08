"""Analysis of the documented high-balance customer proxy."""

from __future__ import annotations

import pandas as pd

from src.analytics import summarize_segments


def high_value_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Compare high-balance proxy customers with other customers."""
    if "HighValueCustomer" not in frame.columns:
        raise KeyError("HighValueCustomer is missing; run feature engineering first.")
    summary = summarize_segments(frame, "HighValueCustomer")
    exposure = frame.assign(
        _churned_balance=frame["Balance"].where(frame["Exited"] == 1, 0.0)
    ).groupby("HighValueCustomer", observed=True).agg(
        balance_exposure=("Balance", "sum"), churned_balance_exposure=("_churned_balance", "sum")
    )
    keys = summary["segment"].map({"True": True, "False": False}).to_numpy()
    summary["balance_exposure"] = exposure["balance_exposure"].reindex(keys).to_numpy()
    summary["churned_balance_exposure"] = exposure["churned_balance_exposure"].reindex(keys).to_numpy()
    return summary


def high_value_customer_detail(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a privacy-conscious high-value customer table without surnames."""
    columns = [
        column
        for column in (
            "CustomerId",
            "Geography",
            "Gender",
            "Age",
            "AgeSegment",
            "Tenure",
            "Balance",
            "EstimatedSalary",
            "NumOfProducts",
            "IsActiveMember",
            "Exited",
        )
        if column in frame.columns
    ]
    return frame.loc[frame["HighValueCustomer"], columns].sort_values("Balance", ascending=False)
