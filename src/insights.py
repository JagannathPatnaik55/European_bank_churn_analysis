"""Generate evidence-linked observations and cautious recommendations."""

from __future__ import annotations

import pandas as pd

from src.analytics import geography_age_analysis, summarize_segments
from src.kpis import calculate_churn_rate, engagement_churn_indicator


def generate_insights(
    frame: pd.DataFrame, minimum_segment_size: int = 100, minimum_rate_difference: float = 0.05
) -> pd.DataFrame:
    """Create findings only when sample size and rate-difference rules are met."""
    overall = calculate_churn_rate(frame["Exited"])
    records: list[dict[str, object]] = []
    dimensions = (
        ("Geography", "country"),
        ("AgeSegment", "age segment"),
        ("TenureGroup", "tenure group"),
        ("CreditScoreSegment", "credit-score segment"),
        ("BalanceSegment", "balance segment"),
        ("Gender", "gender group"),
        ("NumOfProducts", "product-count group"),
    )
    for column, label in dimensions:
        if column not in frame:
            continue
        summary = summarize_segments(frame, column)
        summary = summary[summary["customer_count"] >= minimum_segment_size]
        if summary.empty:
            continue
        risk = summary.sort_values(["churn_rate", "customer_count"], ascending=[False, False]).iloc[0]
        difference = float(risk["churn_rate"] - overall)
        if difference >= minimum_rate_difference:
            if column == "Geography":
                headline = f"{risk['segment']} has an elevated observed churn rate."
            elif column == "AgeSegment":
                headline = f"Customers aged {risk['segment']} have an elevated observed churn rate."
            elif column == "NumOfProducts":
                headline = f"Customers with {risk['segment']} product(s) have an elevated observed churn rate."
            else:
                headline = f"The {risk['segment']} {label} has an elevated observed churn rate."
            records.append(
                {
                    "insight": headline,
                    "evidence": f"{int(risk['churned_count']):,} of {int(risk['customer_count']):,} customers churned ({risk['churn_rate']:.1%}), versus {overall:.1%} overall.",
                    "business_implication": "This segment has a higher observed churn rate than the filtered portfolio.",
                    "recommendation": f"Review this segment's service, product, and engagement experience before designing a targeted retention test.",
                    "dimension": column,
                    "segment": str(risk["segment"]),
                    "sample_size": int(risk["customer_count"]),
                }
            )

    if "Geography" in frame and "AgeSegment" in frame:
        combinations = geography_age_analysis(frame)
        eligible = combinations[combinations["customer_count"] >= minimum_segment_size]
        if not eligible.empty:
            combination = eligible.sort_values(["churn_rate", "customer_count"], ascending=[False, False]).iloc[0]
            difference = float(combination["churn_rate"] - overall)
            if difference >= minimum_rate_difference:
                records.append(
                    {
                        "insight": f"Customers in {combination['Geography']} aged {combination['AgeSegment']} have an elevated observed churn rate.",
                        "evidence": f"{int(combination['churned_count']):,} of {int(combination['customer_count']):,} customers churned ({combination['churn_rate']:.1%}), versus {overall:.1%} overall.",
                        "business_implication": "This geography-age combination has a higher observed churn rate than the filtered portfolio.",
                        "recommendation": "Review the customer journey for this combination and evaluate a targeted retention test before scaling any intervention.",
                        "dimension": "Geography × AgeSegment",
                        "segment": f"{combination['Geography']} · {combination['AgeSegment']}",
                        "sample_size": int(combination["customer_count"]),
                    }
                )

    engagement = engagement_churn_indicator(frame)
    if engagement["inactive_count"] >= minimum_segment_size and engagement["active_count"] >= minimum_segment_size:
        gap = float(engagement["rate_difference"])
        if gap >= minimum_rate_difference:
            records.append(
                {
                    "insight": "Inactive members have a higher observed churn rate than active members.",
                    "evidence": f"Inactive: {engagement['inactive_churn_rate']:.1%} (n={engagement['inactive_count']:,}); active: {engagement['active_churn_rate']:.1%} (n={engagement['active_count']:,}).",
                    "business_implication": "Lower recorded activity co-occurs with higher churn in this snapshot.",
                    "recommendation": "Test proactive engagement outreach and measure subsequent retention before scaling it.",
                    "dimension": "IsActiveMember",
                    "segment": "Inactive",
                    "sample_size": int(engagement["inactive_count"]),
                }
            )

    if not records:
        records.append(
            {
                "insight": "No segment met the minimum evidence thresholds for an automated recommendation.",
                "evidence": f"Required at least {minimum_segment_size} customers and a churn-rate difference of {minimum_rate_difference:.0%} from the filtered portfolio.",
                "business_implication": "Automated segment flags are intentionally suppressed when evidence is weak.",
                "recommendation": "Use the dashboard to inspect rates alongside segment counts and uncertainty before taking action.",
                "dimension": "Portfolio",
                "segment": "All customers",
                "sample_size": int(len(frame)),
            }
        )
    return pd.DataFrame(records)
