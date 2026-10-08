from __future__ import annotations

from src.analytics import summarize_segments
from src.dashboard_filters import apply_filters
from src.high_value_analysis import high_value_customer_detail, high_value_summary
from src.preprocessing import create_segments


def test_segment_summary_separates_rate_and_contribution(sample_data):
    prepared = create_segments(sample_data)
    summary = summarize_segments(prepared, "Geography").set_index("segment")

    assert summary.loc["France", "customer_count"] == 3
    assert summary.loc["France", "churned_count"] == 1
    assert summary.loc["France", "churn_rate"] == 1 / 3
    assert summary.loc["France", "churn_contribution"] == 0.25


def test_binary_segment_dimensions_use_business_labels(sample_data):
    prepared = create_segments(sample_data)
    summary = summarize_segments(prepared, "IsActiveMember")

    assert set(summary["segment"]) == {"Active", "Inactive"}


def test_filtering_combines_dimensions_and_returns_only_matches(sample_data):
    prepared = create_segments(sample_data)
    filtered = apply_filters(prepared, {"Geography": ["Germany"], "AgeSegment": ["46–60"]})

    assert filtered["CustomerId"].tolist() == [3, 4]


def test_unmatched_filters_return_empty_frame_without_error(sample_data):
    prepared = create_segments(sample_data)

    filtered = apply_filters(prepared, {"Geography": ["Atlantis"]})

    assert filtered.empty


def test_high_value_summary_reports_balance_exposure(sample_data):
    prepared = create_segments(sample_data)
    summary = high_value_summary(prepared).set_index("segment")

    assert summary.loc["True", "customer_count"] == 2
    assert summary.loc["True", "churned_count"] == 1
    assert summary.loc["True", "balance_exposure"] == 1100
    assert summary.loc["True", "churned_balance_exposure"] == 600


def test_customer_level_high_value_table_omits_surname(sample_data):
    prepared = create_segments(sample_data)
    detail = high_value_customer_detail(prepared)

    assert "CustomerId" in detail.columns
    assert "Surname" not in detail.columns
    assert detail["Balance"].is_monotonic_decreasing
