from __future__ import annotations

import math

from src.kpis import calculate_churn_rate, calculate_overall_kpis, geographic_risk_index
from src.preprocessing import create_segments


def test_churn_rate_for_two_of_four_customers_is_fifty_percent():
    assert calculate_churn_rate([0, 0, 1, 1]) == 0.5


def test_empty_churn_population_returns_nan():
    assert math.isnan(calculate_churn_rate([]))


def test_overall_kpis_reconcile_counts_and_balance_exposure(sample_data):
    kpis = calculate_overall_kpis(create_segments(sample_data))

    assert kpis["total_customers"] == 8
    assert kpis["churned_customers"] == 4
    assert kpis["retained_customers"] == 4
    assert kpis["overall_churn_rate"] == 0.5
    assert kpis["churned_balance_exposure"] == 1300
    assert kpis["high_value_churn_ratio"] == 0.25


def test_geographic_risk_index_compares_country_to_overall_rate(sample_data):
    risks = geographic_risk_index(sample_data)

    assert risks["Germany"] == 4 / 3
    assert risks["France"] == 2 / 3
