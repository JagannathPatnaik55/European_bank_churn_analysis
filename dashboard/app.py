"""Interactive Streamlit dashboard for European bank churn analysis."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import geography_age_analysis, summarize_segments
from src.config import load_config, resolve_path
from src.dashboard_filters import apply_filters
from src.data_loader import load_data
from src.high_value_analysis import high_value_customer_detail, high_value_summary
from src.insights import generate_insights
from src.kpis import calculate_overall_kpis, geographic_risk_index
from src.preprocessing import create_segments, restore_segment_categories
from dashboard.components import render_empty_state, render_filters, segment_bar


@st.cache_data(show_spinner="Preparing customer analytics…")
def load_dashboard_frame(
    raw_path: str,
    raw_mtime: int,
    processed_path: str,
    processed_mtime: int,
    config_mtime: int,
    credit_quantiles: tuple[float, float],
    high_value_quantile: float,
    age_upper_bounds: tuple[int, int, int],
    age_labels: tuple[str, ...],
    tenure_ranges: tuple[tuple[str, tuple[int, int]], ...],
) -> pd.DataFrame:
    """Load cached processed data, or prepare it from the untouched CSV."""
    processed = Path(processed_path)
    raw = Path(raw_path)
    if processed.exists() and processed_mtime >= max(raw_mtime, config_mtime):
        frame = pd.read_csv(processed)
        if "AgeSegment" in frame and "HighValueCustomer" in frame:
            return restore_segment_categories(frame, list(age_labels))
    return create_segments(
        load_data(raw),
        credit_score_quantiles=credit_quantiles,
        high_value_quantile=high_value_quantile,
        age_upper_bounds=age_upper_bounds,
        age_labels=list(age_labels),
        tenure_groups=dict(tenure_ranges),
    )


def _format_currency(value: float) -> str:
    return f"{value:,.0f}" if pd.notna(value) else "—"


def _render_kpis(frame: pd.DataFrame) -> dict[str, object]:
    kpis = calculate_overall_kpis(frame)
    columns = st.columns(6)
    columns[0].metric("Customers", f"{kpis['total_customers']:,}")
    columns[1].metric("Churned", f"{kpis['churned_customers']:,}")
    columns[2].metric("Churn rate", f"{kpis['overall_churn_rate']:.1%}" if pd.notna(kpis["overall_churn_rate"]) else "—")
    columns[3].metric("Average balance", _format_currency(kpis["average_balance"]))
    columns[4].metric("High-balance churn", f"{kpis['high_value_churn_rate']:.1%}" if pd.notna(kpis["high_value_churn_rate"]) else "—")
    columns[5].metric("Churned balance exposure", _format_currency(kpis["churned_balance_exposure"]))
    st.caption("Balance exposure represents balances held by churned customers; it is not lost revenue.")
    return kpis


def _render_overview(frame: pd.DataFrame) -> None:
    st.title("European Banking Churn Analytics")
    st.caption("A descriptive view of observed customer churn patterns and associated balance exposure.")
    _render_kpis(frame)
    left, right = st.columns(2)
    with left:
        counts = frame["Exited"].value_counts().reindex([0, 1], fill_value=0).rename(index={0: "Retained", 1: "Churned"}).rename_axis("Outcome").reset_index(name="Customers")
        st.plotly_chart(px.pie(counts, names="Outcome", values="Customers", hole=0.58, title="Portfolio outcomes", color="Outcome", color_discrete_map={"Retained": "#547A9B", "Churned": "#D66A55"}), width="stretch")
    with right:
        st.plotly_chart(segment_bar(frame, "Geography", "Country churn rate"), width="stretch")
    dimensions = [("Geography", "Country"), ("AgeSegment", "Age segment"), ("TenureGroup", "Tenure group"), ("BalanceSegment", "Balance segment"), ("NumOfProducts", "Product count")]
    summary = pd.concat([summarize_segments(frame, column).assign(dimension=label) for column, label in dimensions if column in frame], ignore_index=True)
    summary = summary[summary["customer_count"] >= 30].sort_values("churn_rate", ascending=False).head(8)
    st.subheader("Segments with elevated observed churn")
    st.dataframe(summary[["dimension", "segment", "customer_count", "churned_count", "churn_rate", "churn_contribution"]], hide_index=True, width="stretch")
    st.subheader("Evidence-based review priorities")
    for row in generate_insights(frame).head(3).itertuples(index=False):
        with st.container(border=True):
            st.markdown(f"**{row.insight}**")
            st.write(row.evidence)
            st.caption(row.recommendation)


def _render_geography(frame: pd.DataFrame) -> None:
    st.title("Geographic Analytics")
    geo = summarize_segments(frame, "Geography")
    risks = geographic_risk_index(frame)
    geo["geographic_risk_index"] = geo["segment"].map(risks)
    st.dataframe(geo, hide_index=True, width="stretch")
    a, b = st.columns(2)
    with a:
        st.plotly_chart(segment_bar(frame, "Geography", "Country churn rate"), width="stretch")
    with b:
        st.plotly_chart(segment_bar(frame, "Geography", "Country contribution to churn", contribution=True), width="stretch")
    interaction = geography_age_analysis(frame)
    if not interaction.empty:
        pivot = interaction.pivot(index="Geography", columns="AgeSegment", values="churn_rate")
        st.plotly_chart(px.imshow(pivot, text_auto=".1%", color_continuous_scale="Reds", aspect="auto", title="Churn rate by country and age segment", labels={"color": "Churn rate"}), width="stretch")
    financial = frame.groupby("Geography", observed=True).agg(customer_count=("CustomerId", "size"), average_balance=("Balance", "mean"), median_balance=("Balance", "median"), average_salary=("EstimatedSalary", "mean"), average_products=("NumOfProducts", "mean")).reset_index()
    st.subheader("Financial profile by country")
    st.dataframe(financial, hide_index=True, width="stretch")


def _render_demographics(frame: pd.DataFrame) -> None:
    st.title("Demographic & Tenure Analytics")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(segment_bar(frame, "AgeSegment", "Churn by age segment"), width="stretch")
    with right:
        st.plotly_chart(segment_bar(frame, "Gender", "Churn by gender"), width="stretch")
    st.plotly_chart(segment_bar(frame, "TenureGroup", "Churn by tenure"), width="stretch")
    st.subheader("Geography × age detail")
    st.dataframe(geography_age_analysis(frame), hide_index=True, width="stretch")


def _render_financial(frame: pd.DataFrame) -> None:
    st.title("Financial & Engagement Analytics")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(segment_bar(frame, "BalanceSegment", "Churn by balance segment"), width="stretch")
    with right:
        st.plotly_chart(segment_bar(frame, "CreditScoreSegment", "Churn by credit-score segment"), width="stretch")
    a, b = st.columns(2)
    with a:
        st.plotly_chart(segment_bar(frame, "NumOfProducts", "Churn by product count"), width="stretch")
    with b:
        activity = summarize_segments(frame.assign(Activity=frame["IsActiveMember"].map({0: "Inactive", 1: "Active"})), "Activity")
        activity_chart = px.bar(activity, x="segment", y="churn_rate", hover_data=["customer_count", "churned_count"], title="Churn by member activity", labels={"segment": "Activity", "churn_rate": "Churn rate"}, color_discrete_sequence=["#547A9B"])
        activity_chart.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(activity_chart, width="stretch")
    financial = frame.groupby("Exited", observed=True).agg(customer_count=("CustomerId", "size"), average_balance=("Balance", "mean"), median_balance=("Balance", "median"), average_salary=("EstimatedSalary", "mean"), median_salary=("EstimatedSalary", "median"), average_credit_score=("CreditScore", "mean")).reset_index().replace({"Exited": {0: "Retained", 1: "Churned"}})
    st.subheader("Customer financial profile by outcome")
    st.dataframe(financial, hide_index=True, width="stretch")
    interaction = frame.groupby(["NumOfProducts", "ActivityLabel"], observed=True).agg(
        customer_count=("CustomerId", "size"), churned_count=("Exited", "sum"), churn_rate=("Exited", "mean")
    ).reset_index()
    st.subheader("Product × activity interaction")
    st.dataframe(interaction, hide_index=True, width="stretch")
    st.caption("Estimated salary is a profile field; it is not bank revenue.")


def _render_high_value(frame: pd.DataFrame) -> None:
    st.title("High-Balance Customer Explorer")
    summary = high_value_summary(frame)
    high = summary[summary["segment"] == "True"]
    row = high.iloc[0] if len(high) else None
    metrics = st.columns(4)
    metrics[0].metric("High-balance customers", f"{int(row['customer_count']):,}" if row is not None else "0")
    metrics[1].metric("High-balance churners", f"{int(row['churned_count']):,}" if row is not None else "0")
    metrics[2].metric("High-balance churn rate", f"{row['churn_rate']:.1%}" if row is not None else "—")
    metrics[3].metric("Churned balance exposure", _format_currency(row["churned_balance_exposure"]) if row is not None else "0")
    st.caption("High-value is a balance-based proxy: the top quartile of positive balances. It does not measure profitability.")
    st.dataframe(summary, hide_index=True, width="stretch")
    high_customers = frame[frame["HighValueCustomer"]]
    if not high_customers.empty:
        risk_tables = []
        for column, label in (("Geography", "Country"), ("AgeSegment", "Age segment"), ("TenureGroup", "Tenure group")):
            table = summarize_segments(high_customers, column)
            table["dimension"] = label
            risk_tables.append(table)
        high_risk = pd.concat(risk_tables, ignore_index=True)
        high_risk = high_risk[high_risk["customer_count"] >= 30].sort_values("churn_rate", ascending=False).head(8)
        st.subheader("Higher-churn high-balance segments")
        st.dataframe(high_risk[["dimension", "segment", "customer_count", "churned_count", "churn_rate", "churn_contribution"]], hide_index=True, width="stretch")
    detail = high_value_customer_detail(frame)
    st.subheader("Customer-level review table")
    st.caption("Surname is excluded. CustomerId is shown only as a reference key for authorized internal review.")
    st.dataframe(detail, hide_index=True, width="stretch")


def _render_drilldown(frame: pd.DataFrame) -> None:
    st.title("Segment Drill-down")
    dimensions = {"Geography": "Geography", "Age": "AgeSegment", "Credit score": "CreditScoreSegment", "Tenure": "TenureGroup", "Balance": "BalanceSegment", "Gender": "Gender", "Activity": "ActivityLabel", "Product count": "NumOfProducts"}
    label = st.selectbox("Segmentation dimension", list(dimensions))
    column = dimensions[label]
    summary = summarize_segments(frame, column)
    selected = st.selectbox("Segment", summary["segment"].tolist())
    row = summary[summary["segment"] == selected].iloc[0]
    chosen = frame[frame[column].astype("string") == str(selected)]
    metrics = st.columns(4)
    metrics[0].metric("Segment customers", f"{int(row['customer_count']):,}")
    metrics[1].metric("Segment churn rate", f"{row['churn_rate']:.1%}")
    metrics[2].metric("Share of all churners", f"{row['churn_contribution']:.1%}")
    metrics[3].metric("Risk index vs portfolio", f"{row['churn_index']:.2f}" if pd.notna(row["churn_index"]) else "—")
    st.plotly_chart(segment_bar(frame, column, f"{label} segment comparison"), width="stretch")
    st.subheader("Financial profile for this segment")
    profile = chosen.groupby("Exited", observed=True).agg(customer_count=("CustomerId", "size"), average_balance=("Balance", "mean"), median_balance=("Balance", "median"), average_salary=("EstimatedSalary", "mean"), average_tenure=("Tenure", "mean")).reset_index().replace({"Exited": {0: "Retained", 1: "Churned"}})
    st.dataframe(profile, hide_index=True, width="stretch")


def _render_insights(frame: pd.DataFrame) -> None:
    st.title("Insights & Recommendations")
    st.caption("Automated observations require a minimum segment size and churn-rate difference; they describe association, not cause.")
    for row in generate_insights(frame).itertuples(index=False):
        with st.container(border=True):
            st.subheader(row.insight)
            st.write(f"**Evidence:** {row.evidence}")
            st.write(f"**Business implication:** {row.business_implication}")
            st.write(f"**Suggested next step:** {row.recommendation}")
            st.caption(f"Dimension: {row.dimension} · Segment: {row.segment} · n={row.sample_size:,}")


def main() -> None:
    config = load_config()
    st.set_page_config(page_title=config.get("dashboard", {}).get("page_title", "Churn Analytics"), page_icon="🏦", layout="wide")
    css_path = ROOT / "dashboard" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    st.sidebar.title("European Bank")
    st.sidebar.caption("Customer retention analytics")
    if st.sidebar.button("Refresh source data", width="stretch"):
        load_dashboard_frame.clear()
        st.rerun()
    raw_path = resolve_path(config, "raw_data")
    processed_path = resolve_path(config, "processed_data")
    if not raw_path.exists():
        st.error("Dataset not found. Please place European_Bank.csv in data/raw/.")
        st.stop()
    try:
        settings = config.get("segmentation", {})
        quantiles = tuple(float(value) for value in settings.get("credit_score_quantiles", [1 / 3, 2 / 3]))
        age_bounds = tuple(int(value) for value in settings.get("age_upper_bounds", [29, 45, 60]))
        age_labels = tuple(str(value) for value in settings.get("age_labels", ["<30", "30–45", "46–60", "60+"]))
        tenure_ranges = tuple((name, tuple(int(value) for value in bounds)) for name, bounds in settings.get("tenure_groups", {"New": [0, 2], "Mid-term": [3, 6], "Long-term": [7, 10]}).items())
        config_path = ROOT / "config.yaml"
        frame = load_dashboard_frame(str(raw_path), raw_path.stat().st_mtime_ns, str(processed_path), processed_path.stat().st_mtime_ns if processed_path.exists() else 0, config_path.stat().st_mtime_ns, quantiles, float(settings.get("balance_high_value_quantile", 0.75)), age_bounds, age_labels, tenure_ranges)
    except Exception as exc:
        error = str(exc) if config.get("dashboard", {}).get("debug") else "check the source CSV and data-quality report."
        st.error(f"Unable to load customer analytics: {error}")
        st.stop()
    filters = render_filters(st, frame)
    selected = apply_filters(frame, filters)
    page = st.sidebar.radio("Analytics view", ["Executive Overview", "Geographic Analytics", "Demographic & Tenure", "Financial & Engagement", "High-Value Explorer", "Segment Drill-down", "Insights & Recommendations"])
    if selected.empty:
        render_empty_state(st)
        st.stop()
    if page == "Executive Overview":
        _render_overview(selected)
    elif page == "Geographic Analytics":
        _render_geography(selected)
    elif page == "Demographic & Tenure":
        _render_demographics(selected)
    elif page == "Financial & Engagement":
        _render_financial(selected)
    elif page == "High-Value Explorer":
        _render_high_value(selected)
    elif page == "Segment Drill-down":
        _render_drilldown(selected)
    else:
        _render_insights(selected)
    st.sidebar.markdown("---")
    year = int(frame["Year"].iloc[0]) if "Year" in frame and len(frame) else "unknown"
    st.sidebar.caption(f"Showing {len(selected):,} of {len(frame):,} customers · source snapshot year {year}")


if __name__ == "__main__":
    main()
