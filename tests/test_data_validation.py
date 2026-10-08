from __future__ import annotations

import pandas as pd
import pytest

from src.data_loader import load_data
from src.data_validation import REQUIRED_COLUMNS, validate_data, validate_schema


def test_load_data_reads_csv_and_preserves_all_rows(sample_data, tmp_path):
    path = tmp_path / "customers.csv"
    sample_data.to_csv(path, index=False)

    loaded = load_data(path)

    assert len(loaded) == len(sample_data)
    assert loaded.columns.tolist() == sample_data.columns.tolist()


def test_missing_dataset_error_is_actionable(tmp_path):
    path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError, match="Dataset not found"):
        load_data(path)


def test_schema_error_names_missing_target(sample_data):
    with pytest.raises(ValueError, match="missing column 'Exited'"):
        validate_schema(sample_data.drop(columns="Exited"))


def test_required_schema_matches_business_dataset():
    assert "Exited" in REQUIRED_COLUMNS
    assert "CustomerId" in REQUIRED_COLUMNS
    assert "Year" not in REQUIRED_COLUMNS


def test_quality_report_detects_issues_without_deleting_rows(sample_data):
    bad = pd.concat([sample_data, sample_data.iloc[[0]]], ignore_index=True)
    bad.loc[1, "Balance"] = -10
    bad.loc[2, "Exited"] = 2

    result = validate_data(bad)

    assert result.row_count == 9
    assert result.duplicate_rows == 1
    assert result.duplicate_customer_ids == 1
    assert result.is_valid is False
    assert len(result.issues) >= 3


def test_quality_report_documents_types_ranges_and_categories(sample_data):
    result = validate_data(sample_data)
    report = result.to_markdown()

    assert result.dtypes["Age"].startswith("int")
    assert result.numeric_ranges["Age"] == {"min": 25.0, "max": 70.0}
    assert result.categorical_values["Geography"] == ["France", "Germany", "Spain"]
    assert "Numeric ranges" in report
    assert "Geography values" in report
    assert "PASS WITH NOTES" in report


def test_quality_report_flags_unrecognized_geography(sample_data):
    sample_data.loc[0, "Geography"] = "Portugal"

    result = validate_data(sample_data)

    assert any(issue.code == "invalid_category" and issue.count == 1 for issue in result.issues)
