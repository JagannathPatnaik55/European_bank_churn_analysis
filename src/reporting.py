"""Stakeholder reports generated from live pipeline outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.data_validation import ValidationResult


def _pct(value: object) -> str:
    return f"{float(value):.1%}" if pd.notna(value) else "Not available"


def _number(value: object) -> str:
    return f"{float(value):,.2f}" if pd.notna(value) else "Not available"


def _markdown_table(frame: pd.DataFrame, digits: int = 3) -> str:
    """Render a compact Markdown table without an optional formatter dependency."""
    if frame.empty:
        return "No rows available."
    headers = [str(column) for column in frame.columns]
    rows: list[list[str]] = []
    for row in frame.itertuples(index=False, name=None):
        cells = []
        for value in row:
            if pd.isna(value):
                cells.append("")
            elif isinstance(value, (float, int)) and not isinstance(value, bool):
                cells.append(f"{value:.{digits}f}" if isinstance(value, float) else f"{value:,}")
            else:
                cells.append(str(value).replace("|", "\\|"))
        rows.append(cells)
    widths = [max(len(headers[index]), *(len(row[index]) for row in rows)) for index in range(len(headers))]
    header = "| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(headers)) + " |"
    separator = "| " + " | ".join("-" * widths[index] for index in range(len(headers))) + " |"
    body = ["| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(row)) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _top_segment(table: pd.DataFrame | None) -> pd.Series | None:
    if table is None or table.empty:
        return None
    return table.sort_values(["churn_rate", "customer_count"], ascending=[False, False]).iloc[0]


def generate_report_bundle(
    report_dir: str | Path,
    frame: pd.DataFrame,
    kpis: dict[str, Any],
    validation: ValidationResult,
    segment_summaries: dict[str, pd.DataFrame],
    high_value: pd.DataFrame,
    statistics: pd.DataFrame,
    insights: pd.DataFrame,
    segment_definitions: dict[str, Any] | None = None,
) -> dict[str, Path]:
    """Write executive, research, and data-quality Markdown reports."""
    directory = Path(report_dir)
    directory.mkdir(parents=True, exist_ok=True)
    quality_path = directory / "data_quality_report.md"
    quality_path.write_text(validation.to_markdown(), encoding="utf-8")

    geography = _top_segment(segment_summaries.get("Geography"))
    age = _top_segment(segment_summaries.get("AgeSegment"))
    tenure = _top_segment(segment_summaries.get("TenureGroup"))
    hv = high_value.loc[high_value["segment"] == "True"] if not high_value.empty else pd.DataFrame()
    hv_row = hv.iloc[0] if len(hv) else None
    definitions = segment_definitions or {}
    age_definition = definitions.get("age", {"<30": "18–29", "30–45": "30–45", "46–60": "46–60", "60+": "61+"})
    credit_definition = definitions.get("credit_score", {"method": "sample tertiles"})
    tenure_definition = definitions.get("tenure", {"New": "0–2 years", "Mid-term": "3–6 years", "Long-term": "7–10 years"})
    balance_definition = definitions.get("balance", {})
    high_value_definition = definitions.get("high_value_customer", {})
    year_text = str(int(frame["Year"].dropna().iloc[0])) if "Year" in frame and frame["Year"].notna().any() else "not supplied"
    summary_lines = [
        "# Executive Summary for Government Stakeholders — European Banking Churn Analytics",
        "",
        f"## Scope and snapshot",
        "",
        f"This descriptive analysis covers **{kpis['total_customers']:,} customer records** from the supplied {year_text} snapshot. It measures observed churn patterns and balance exposure; the data does not establish causal drivers or customer revenue.",
        "",
        "## Portfolio KPIs",
        "",
        f"- Customers: {kpis['total_customers']:,}",
        f"- Churned: {kpis['churned_customers']:,} ({_pct(kpis['overall_churn_rate'])})",
        f"- Retained: {kpis['retained_customers']:,}",
        f"- Average account balance: {_number(kpis['average_balance'])}",
        f"- Churned-customer balance exposure: {_number(kpis['churned_balance_exposure'])} ({_pct(kpis['churned_balance_share'])} of observed portfolio balance)",
        f"- High-balance proxy churn rate: {_pct(kpis['high_value_churn_rate'])}",
        f"- High-balance proxy share of churners: {_pct(kpis['high_value_churn_ratio'])}",
        "",
        "## Observed patterns",
        "",
    ]
    if geography is not None:
        summary_lines.append(f"- Highest country churn rate: **{geography['segment']}**, {_pct(geography['churn_rate'])} across {int(geography['customer_count']):,} customers; churn contribution is {_pct(geography['churn_contribution'])}.")
    if age is not None:
        summary_lines.append(f"- Highest age-segment churn rate: **{age['segment']}**, {_pct(age['churn_rate'])} across {int(age['customer_count']):,} customers.")
    if tenure is not None:
        summary_lines.append(f"- Highest tenure-group churn rate: **{tenure['segment']}**, {_pct(tenure['churn_rate'])} across {int(tenure['customer_count']):,} customers.")
    if hv_row is not None:
        summary_lines.append(f"- The high-balance proxy includes {int(hv_row['customer_count']):,} customers; {int(hv_row['churned_count']):,} churned, with {_pct(hv_row['churn_rate'])} churn and {_number(hv_row['churned_balance_exposure'])} of balance exposure held by those churners.")
    summary_lines.extend(["", "## Retention priorities for evaluation", ""])
    for row in insights.head(5).itertuples(index=False):
        summary_lines.extend([f"### {row.insight}", "", f"**Evidence:** {row.evidence}", "", f"**Suggested next step:** {row.recommendation}", ""])
    summary_lines.extend(
        [
            "## Interpretation limits",
            "",
            "- This is a single-period customer snapshot with no transaction, service-contact, product-profitability, or historical event data.",
            "- Churn rates describe observed association. They should not be interpreted as causal effects or validated future churn probabilities.",
            "- Account balances are shown as balance exposure, not revenue, profit, or recoverable value.",
            "- The high-value cohort is a transparent high-balance proxy; it is not a complete customer lifetime-value measure.",
        ]
    )
    executive_path = directory / "executive_summary.md"
    executive_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    lines = [
        "# Customer Segmentation & Churn Pattern Analytics in European Banking",
        "",
        "## Executive Summary",
        "",
        f"The supplied snapshot contains {kpis['total_customers']:,} customers and an observed churn rate of {_pct(kpis['overall_churn_rate'])}. The analysis compares churn by country, age, tenure, credit score, balance, gender, product ownership, and activity. It reports association and balance exposure without making causal or revenue claims.",
        "",
        "## Introduction",
        "",
        "Customer retention is a relevant operating concern for retail banks. This project organizes customer-level churn patterns into interpretable portfolio and segment measures.",
        "",
        "## Background and Context",
        "",
        "The project brief frames churn as a source of potential lifetime-value and acquisition pressure. The supplied data does not include realized income, costs, or customer-level profitability, so those impacts cannot be quantified here.",
        "",
        "## Problem Statement",
        "",
        "Portfolio churn rates alone do not show how churn is distributed across customer groups or how the financial profile of churners compares with retained customers.",
        "",
        "## Objectives",
        "",
        "- Measure total churn and segment churn rates.",
        "- Compare churn contribution separately from segment churn rate.",
        "- Describe geography, demographic, financial, tenure, product, and engagement patterns.",
        "- Quantify associated account-balance exposure and produce evidence-linked review priorities.",
        "",
        "## Dataset Description",
        "",
        f"The analysis uses {validation.row_count:,} rows and {validation.column_count} supplied columns. `Exited` is the binary outcome (1 = churned, 0 = retained). `Year` is present as a constant snapshot field in the CSV but absent from the DOCX schema table; it is retained as provenance and excluded from explanatory segmentation.",
        "",
        "## Data Quality Assessment",
        "",
        f"Missing cells: {sum(validation.missing_values.values()):,}; duplicate rows: {validation.duplicate_rows:,}; duplicate customer identifiers beyond the first occurrence: {validation.duplicate_customer_ids:,}. See [data_quality_report.md](data_quality_report.md) for the complete checks and findings. No records are deleted based on statistical outlier status.",
        "",
        "## Analytical Methodology",
        "",
        "Churn rates use churned customers divided by all customers in the relevant population. Churn contribution uses churners in the segment divided by all churners. The geographic risk index is the country churn rate divided by the portfolio churn rate. Categorical associations use chi-square tests with Cramér’s V; numeric distributions use two-sided Mann–Whitney U tests. Reported p-values use a Holm family-wise adjustment across the planned tests. Statistical significance is not evidence of causality.",
        "",
        "## Customer Segmentation Framework",
        "",
        f"- Age: {'; '.join(f'`{label}` = {bounds}' for label, bounds in age_definition.items())}. Groups are disjoint.",
        f"- Credit score: Low / Medium / High using {credit_definition.get('method', 'configured score bands')}; cutoffs {credit_definition.get('low_cutoff', 'n/a')} and {credit_definition.get('high_cutoff', 'n/a')}.",
        f"- Tenure: {'; '.join(f'{label} = {bounds}' for label, bounds in tenure_definition.items())}.",
        f"- Balance: zero balance; low positive balance through {balance_definition.get('positive_balance_median', 'the positive-balance median')}; high positive balance above that value.",
        f"- High-value proxy: positive-balance customers at or above the configured {high_value_definition.get('method', 'upper-quartile threshold')} (balance threshold {high_value_definition.get('balance_threshold', 'n/a')}). It is a high-balance screen, not a profitability classification.",
        "",
    ]
    for title, dimension in [
        ("Exploratory Data Analysis", None),
        ("Overall Churn Analysis", None),
        ("Geographic Analysis", "Geography"),
        ("Demographic Analysis", "Gender"),
        ("Age and Tenure Analysis", "AgeSegment"),
        ("Credit Score Analysis", "CreditScoreSegment"),
        ("Financial Profile Analysis", "BalanceSegment"),
        ("Engagement Analysis", "IsActiveMember"),
        ("Product Analysis", "NumOfProducts"),
        ("High-Value Customer Analysis", None),
        ("Balance Exposure Analysis", None),
        ("KPI Framework", None),
    ]:
        lines.extend([f"## {title}", ""])
        if title == "Exploratory Data Analysis":
            lines.append(f"The raw snapshot contains {validation.row_count:,} observations, {validation.column_count} columns, {kpis['churned_customers']:,} churners, and {kpis['retained_customers']:,} retained customers.")
        elif title == "Overall Churn Analysis":
            lines.append(f"Observed churn is {kpis['churned_customers']:,} / {kpis['total_customers']:,} = {_pct(kpis['overall_churn_rate'])}.")
        elif title == "High-Value Customer Analysis":
            lines.append(f"The high-balance proxy has {kpis['high_value_customer_count']:,} customers, {kpis['high_value_churned_count']:,} churners, and {_pct(kpis['high_value_churn_rate'])} churn. These customers represent {_pct(kpis['high_value_churn_ratio'])} of churners; their churned balance exposure is {_number(kpis['high_value_churn_balance_exposure'])}.")
        elif title == "Balance Exposure Analysis":
            lines.append(f"Churned customers held {_number(kpis['churned_balance_exposure'])} in observed account balance, equal to {_pct(kpis['churned_balance_share'])} of total observed balance. This is not a lost-revenue estimate.")
        elif title == "KPI Framework":
            lines.append("Portfolio churn rate = churned / total; segment churn rate = segment churned / segment customers; churn contribution = segment churned / portfolio churned; geographic risk index = country churn rate / portfolio churn rate; engagement indicator = inactive churn rate compared with active churn rate.")
        elif dimension and dimension in segment_summaries:
            table = segment_summaries[dimension]
            lines.append(_markdown_table(table[["segment", "customer_count", "churned_count", "churn_rate", "churn_contribution", "churn_index"]]))
        lines.append("")
    lines.extend(
        [
            "## Statistical Results",
            "",
            _markdown_table(statistics, digits=4) if not statistics.empty else "No statistical tests were estimable.",
            "",
            "## Key Findings",
            "",
        ]
    )
    for row in insights.itertuples(index=False):
        lines.extend([f"- **{row.insight}** {row.evidence} {row.business_implication}"])
    lines.extend(["", "## Business Implications", "", "The segment comparisons can help prioritize follow-up investigation, but intervention decisions should consider customer experience, operational capacity, fairness, and outcomes from controlled retention evaluations.", "", "## Recommendations", ""])
    for row in insights.itertuples(index=False):
        lines.append(f"- {row.recommendation}")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "This is a single-period snapshot without transaction history, churn timing, profitability, revenue-per-customer, service interactions, marketing exposure, or observed retention interventions. Findings are descriptive and do not establish causality or forward-looking risk.",
            "",
            "## Conclusion",
            "",
            f"The supplied snapshot has an observed churn rate of {_pct(kpis['overall_churn_rate'])}. Geographic, demographic, financial, engagement, and product summaries identify where churn is concentrated and where rates are elevated, subject to the sample sizes and limitations reported above.",
            "",
            "## Technical Appendix",
            "",
            "Generated CSV tables are in `data/outputs/`; static figures are in `reports/figures/`. Pipeline code and segmentation thresholds are centralized in the project source and configuration.",
        ]
    )
    research_path = directory / "research_paper.md"
    research_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"data_quality_report": quality_path, "executive_summary": executive_path, "research_paper": research_path}
