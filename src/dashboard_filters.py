"""Filter functions shared by the dashboard and automated checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd


FILTER_COLUMNS = (
    "Geography",
    "Gender",
    "AgeSegment",
    "CreditScoreSegment",
    "TenureGroup",
    "BalanceSegment",
    "IsActiveMember",
    "HasCrCard",
    "NumOfProducts",
    "Exited",
    "HighValueCustomer",
)


def apply_filters(frame: pd.DataFrame, filters: Mapping[str, object] | None) -> pd.DataFrame:
    """Apply selected values conjunctively; empty selections mean all values."""
    result = frame
    for column, selected in (filters or {}).items():
        if selected is None or column not in result.columns:
            continue
        if isinstance(selected, (str, bytes)) or not isinstance(selected, Sequence):
            values = [selected]
        else:
            values = list(selected)
        if values:
            result = result[result[column].isin(values)]
    return result.copy()
