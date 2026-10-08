from __future__ import annotations

from src.insights import generate_insights
from src.preprocessing import create_segments
from src.statistical_analysis import run_statistical_analysis


def test_insight_engine_suppresses_segments_below_minimum_sample(sample_data):
    prepared = create_segments(sample_data)
    insights = generate_insights(prepared, minimum_segment_size=100, minimum_rate_difference=0.05)

    assert len(insights) == 1
    assert "No segment met" in insights.iloc[0]["insight"]


def test_statistical_analysis_includes_hypothesis_and_effect_size(sample_data):
    prepared = create_segments(sample_data)
    results = run_statistical_analysis(prepared)

    geography = results.loc[results["variable"] == "Geography"].iloc[0]
    assert "independent" in geography["null_hypothesis"]
    assert geography["n"] == len(sample_data)
    assert 0 <= geography["effect_size"] <= 1
    assert 0 <= geography["p_value"] <= 1
    assert 0 <= geography["p_value_adjusted"] <= 1
    assert geography["significant"] in (True, False)


def test_insight_text_uses_clear_segment_wording(sample_data):
    prepared = create_segments(sample_data)
    insights = generate_insights(prepared, minimum_segment_size=1, minimum_rate_difference=0.05)

    assert any("Germany" in value and "elevated observed churn" in value for value in insights["insight"])


def test_insight_engine_can_identify_a_geography_age_combination(sample_data):
    prepared = create_segments(sample_data)
    insights = generate_insights(prepared, minimum_segment_size=1, minimum_rate_difference=0.05)

    assert any("Germany" in value and "age" in value.lower() for value in insights["insight"])
