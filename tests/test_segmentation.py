from __future__ import annotations

from src.preprocessing import (
    assign_balance_segment,
    assign_credit_score_segment,
    assign_high_value_flag,
    assign_tenure_group,
    create_segments,
    restore_segment_categories,
    segment_age,
)
import pandas as pd


def test_age_segments_are_disjoint_and_follow_documented_age_60_boundary():
    result = segment_age([18, 29, 30, 45, 46, 60, 61])

    assert result.astype(str).tolist() == ["<30", "<30", "30–45", "30–45", "46–60", "46–60", "60+"]


def test_tenure_groups_have_explicit_inclusive_ranges():
    result = assign_tenure_group([0, 2, 3, 6, 7, 10])

    assert result.astype(str).tolist() == ["New", "New", "Mid-term", "Mid-term", "Long-term", "Long-term"]


def test_credit_score_segments_are_ordered_and_cover_observed_values():
    result, thresholds = assign_credit_score_segment([300, 400, 500, 600, 700, 800, 900])

    assert set(result.astype(str)) == {"Low", "Medium", "High"}
    assert thresholds["low_cutoff"] < thresholds["high_cutoff"]


def test_balance_segments_separate_zero_from_positive_balance():
    result = assign_balance_segment([0, 100, 200, 300, 400])

    assert result.astype(str).tolist() == ["Zero-balance", "Low-balance", "Low-balance", "High-balance", "High-balance"]


def test_high_value_proxy_uses_positive_balance_upper_quartile():
    result, threshold = assign_high_value_flag([0, 100, 200, 300, 400])

    assert threshold == 325
    assert result.tolist() == [False, False, False, False, True]


def test_create_segments_preserves_source_and_excludes_surname(sample_data):
    result = create_segments(sample_data)

    assert "Surname" not in result.columns
    assert "AgeSegment" in result.columns
    assert "HighValueCustomer" in result.columns
    assert len(result) == len(sample_data)


def test_restoring_processed_csv_reinstates_segment_order(sample_data, tmp_path):
    prepared = create_segments(sample_data)
    path = tmp_path / "processed.csv"
    prepared.to_csv(path, index=False)
    reloaded = restore_segment_categories(pd.read_csv(path))

    assert reloaded["AgeSegment"].cat.categories.tolist() == ["<30", "30–45", "46–60", "60+"]
    assert reloaded["TenureGroup"].cat.categories.tolist() == ["New", "Mid-term", "Long-term"]
