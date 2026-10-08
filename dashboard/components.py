"""Reusable Streamlit controls and chart helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px

from src.analytics import summarize_segments
from src.dashboard_filters import FILTER_COLUMNS


FILTER_LABELS = {
    "AgeSegment": "Age segment",
    "CreditScoreSegment": "Credit-score segment",
    "TenureGroup": "Tenure group",
    "BalanceSegment": "Balance segment",
    "IsActiveMember": "Member activity",
    "HasCrCard": "Credit-card ownership",
    "NumOfProducts": "Product count",
    "Exited": "Churn status",
    "HighValueCustomer": "High-balance proxy",
}


def _options(frame: pd.DataFrame, column: str) -> list[Any]:
    series = frame[column]
    if isinstance(series.dtype, pd.CategoricalDtype):
        return [value for value in series.cat.categories if value in set(series.dropna())]
    return sorted(series.dropna().unique().tolist(), key=lambda value: str(value))


def _display_value(column: str, value: Any) -> str:
    if column == "Exited":
        return "Churned" if int(value) == 1 else "Retained"
    if column == "IsActiveMember":
        return "Active" if int(value) == 1 else "Inactive"
    if column == "HasCrCard":
        return "Credit card holder" if int(value) == 1 else "No credit card"
    if column == "HighValueCustomer":
        return "High-balance proxy" if bool(value) else "Other customers"
    return str(value)


def render_filters(st: Any, frame: pd.DataFrame) -> dict[str, list[Any]]:
    """Render all dashboard filters and a working reset control."""
    st.sidebar.header("Portfolio filters")
    options_by_column = {column: _options(frame, column) for column in FILTER_COLUMNS if column in frame}
    if st.sidebar.button("Reset filters", width="stretch"):
        for column, options in options_by_column.items():
            st.session_state[f"filter_{column}"] = options
        st.rerun()
    filters: dict[str, list[Any]] = {}
    for column, options in options_by_column.items():
        key = f"filter_{column}"
        if key in st.session_state:
            selected = [value for value in st.session_state[key] if value in options]
        else:
            selected = options
        filters[column] = st.sidebar.multiselect(
            FILTER_LABELS.get(column, column),
            options=options,
            default=selected,
            format_func=lambda value, field=column: _display_value(field, value),
            key=key,
        )
    return filters


def segment_bar(frame: pd.DataFrame, column: str, title: str, *, contribution: bool = False):
    """Build a reusable segment churn-rate or contribution chart."""
    summary = summarize_segments(frame, column)
    y_column = "churn_contribution" if contribution else "churn_rate"
    fig = px.bar(
        summary,
        x="segment",
        y=y_column,
        hover_data=["customer_count", "churned_count", "retained_count"],
        title=title or f"{column} comparison",
        labels={"segment": "Segment", y_column: "Share of churners" if contribution else "Churn rate"},
        color_discrete_sequence=["#547A9B"],
    )
    fig.update_layout(margin=dict(l=8, r=8, t=48, b=8), yaxis_tickformat=".0%")
    return fig


def render_empty_state(st: Any) -> None:
    """Show the standard empty-filter message."""
    st.info("No customers match the selected filters.")
