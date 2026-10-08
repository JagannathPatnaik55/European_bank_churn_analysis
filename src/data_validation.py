"""Schema, range, and data-quality checks that never drop observations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = (
    "CustomerId",
    "Surname",
    "CreditScore",
    "Geography",
    "Gender",
    "Age",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "HasCrCard",
    "IsActiveMember",
    "EstimatedSalary",
    "Exited",
)
BINARY_COLUMNS = ("HasCrCard", "IsActiveMember", "Exited")
CATEGORICAL_VALUES = {"Geography": {"France", "Germany", "Spain"}, "Gender": {"Female", "Male"}}
NUMERIC_RANGES = {
    "CreditScore": (300, 850),
    "Age": (18, 120),
    "Tenure": (0, 10),
    "Balance": (0, None),
    "NumOfProducts": (1, 4),
    "EstimatedSalary": (0, None),
}


@dataclass
class ValidationIssue:
    """One human-readable data-quality finding."""

    code: str
    severity: str
    count: int
    message: str


@dataclass
class ValidationResult:
    """Summary of validation results, including non-fatal unusual values."""

    row_count: int
    column_count: int
    missing_values: dict[str, int] = field(default_factory=dict)
    duplicate_rows: int = 0
    duplicate_customer_ids: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)
    dtypes: dict[str, str] = field(default_factory=dict)
    unique_counts: dict[str, int] = field(default_factory=dict)
    numeric_ranges: dict[str, dict[str, float]] = field(default_factory=dict)
    categorical_values: dict[str, list[str]] = field(default_factory=dict)
    binary_distributions: dict[str, dict[str, int]] = field(default_factory=dict)
    target_distribution: dict[str, int] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Return false when a blocking data-quality error was detected."""
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def status(self) -> str:
        """Distinguish clean validation from a pass that includes notes."""
        if not self.is_valid:
            return "REVIEW REQUIRED"
        return "PASS WITH NOTES" if self.issues else "PASS"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable quality summary."""
        result = asdict(self)
        result["issues"] = [asdict(issue) for issue in self.issues]
        result["is_valid"] = self.is_valid
        result["status"] = self.status
        return result

    def to_markdown(self) -> str:
        """Render a concise, human-readable quality report."""
        lines = [
            "# Data Quality Report",
            "",
            f"- Rows: {self.row_count:,}",
            f"- Columns: {self.column_count:,}",
            f"- Duplicate rows: {self.duplicate_rows:,}",
            f"- Duplicate CustomerId values: {self.duplicate_customer_ids:,}",
            f"- Validation status: {self.status}",
            "",
            "## Schema and missing values",
            "",
            "| Column | Type | Unique values | Missing |",
            "|---|---|---:|---:|",
        ]
        lines.extend(
            f"| {column} | {self.dtypes.get(column, 'unknown')} | {self.unique_counts.get(column, 0):,} | {count:,} |"
            for column, count in self.missing_values.items()
        )
        lines.extend(["", "## Numeric ranges", "", "| Column | Minimum | Maximum |", "|---|---:|---:|"])
        lines.extend(f"| {column} | {values['min']:,.2f} | {values['max']:,.2f} |" for column, values in self.numeric_ranges.items())
        lines.extend(["", "## Categorical values", ""])
        lines.extend(f"- **{column} values:** {', '.join(values) if values else 'No observed values'}" for column, values in self.categorical_values.items())
        lines.extend(["", "## Binary-field distributions", "", "| Field | Values and counts |", "|---|---|"])
        lines.extend(f"| {column} | {', '.join(f'{value}: {count:,}' for value, count in distribution.items())} |" for column, distribution in self.binary_distributions.items())
        lines.extend(["", "## Findings", ""])
        if self.issues:
            lines.extend(f"- **{issue.severity.upper()} — {issue.code}:** {issue.message} ({issue.count:,})" for issue in self.issues)
        else:
            lines.append("No validation issues were detected.")
        lines.extend(
            [
                "",
            "## Checks performed",
            "",
            "Required schema, missing cells, exact duplicate rows, CustomerId uniqueness, geography/gender domains, binary values, and numeric ranges were checked. The target is expected to use 0 = retained and 1 = churned.",
            "",
            "## Handling rule",
                "",
                "Validation reports suspicious or unusual observations; it does not delete records. Statistical outliers within valid ranges are retained.",
                "",
                "## Target distribution",
                "",
                "| Exited | Customers |",
                "|---:|---:|",
            ]
        )
        lines.extend(f"| {label} | {count:,} |" for label, count in self.target_distribution.items())
        return "\n".join(lines) + "\n"


def validate_schema(frame: pd.DataFrame) -> None:
    """Raise a useful error when required business fields are absent."""
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Dataset schema validation failed: missing column '{missing[0]}'.")


def validate_data(frame: pd.DataFrame) -> ValidationResult:
    """Check dataset shape, key uniqueness, domains, binary fields, and ranges."""
    validate_schema(frame)
    issues: list[ValidationIssue] = []
    missing_values = {str(column): int(count) for column, count in frame.isna().sum().items()}
    for column, count in missing_values.items():
        if count:
            issues.append(ValidationIssue("missing_values", "error", count, f"{column} contains missing values."))

    duplicate_rows = int(frame.duplicated().sum())
    if duplicate_rows:
        issues.append(ValidationIssue("duplicate_rows", "warning", duplicate_rows, "Exact duplicate rows were found and retained."))
    duplicate_ids = int(frame["CustomerId"].duplicated().sum())
    if duplicate_ids:
        issues.append(ValidationIssue("duplicate_customer_ids", "error", duplicate_ids, "CustomerId is not unique; investigate before customer-level interpretation."))

    categorical_values: dict[str, list[str]] = {}
    for column, allowed in CATEGORICAL_VALUES.items():
        observed = set(frame[column].dropna().astype(str).unique())
        categorical_values[column] = sorted(observed)
        invalid = int((frame[column].notna() & ~frame[column].astype(str).isin(allowed)).sum())
        if invalid:
            issues.append(ValidationIssue("invalid_category", "error", invalid, f"{column} contains values outside {sorted(allowed)}."))

    binary_distributions: dict[str, dict[str, int]] = {}
    for column in BINARY_COLUMNS:
        counts = frame[column].value_counts(dropna=False)
        binary_distributions[column] = {str(value): int(count) for value, count in sorted(counts.items(), key=lambda item: str(item[0]))}
        invalid = int((frame[column].notna() & ~frame[column].isin([0, 1])).sum())
        if invalid:
            issues.append(ValidationIssue("invalid_binary", "error", invalid, f"{column} must contain only 0 or 1."))

    numeric_ranges: dict[str, dict[str, float]] = {}
    for column, (minimum, maximum) in NUMERIC_RANGES.items():
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.notna().any():
            numeric_ranges[column] = {"min": float(values.min()), "max": float(values.max())}
        invalid = values.isna() & frame[column].notna()
        if minimum is not None:
            invalid |= values < minimum
        if maximum is not None:
            invalid |= values > maximum
        invalid_count = int(invalid.sum())
        if invalid_count:
            issues.append(ValidationIssue("invalid_range", "error", invalid_count, f"{column} contains values outside [{minimum}, {maximum}]."))

    for column in ("CreditScore", "Age", "NumOfProducts"):
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        if len(values) >= 4:
            q1, q3 = values.quantile([0.25, 0.75])
            lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
            outliers = int(((values < lower) | (values > upper)).sum())
            if outliers:
                issues.append(ValidationIssue("statistical_outlier", "info", outliers, f"{column} has values outside the 1.5×IQR fences; in-range observations are retained."))

    if "Year" in frame.columns and frame["Year"].nunique(dropna=True) <= 1:
        issues.append(ValidationIssue("constant_year", "info", int(frame["Year"].nunique()), "Year is constant in this file and is treated as snapshot provenance, not an explanatory feature."))

    target_counts = frame["Exited"].value_counts(dropna=False)
    target_distribution = {str(label): int(count) for label, count in sorted(target_counts.items(), key=lambda item: str(item[0]))}
    return ValidationResult(
        row_count=int(len(frame)),
        column_count=int(frame.shape[1]),
        missing_values=missing_values,
        duplicate_rows=duplicate_rows,
        duplicate_customer_ids=duplicate_ids,
        issues=issues,
        dtypes={str(column): str(dtype) for column, dtype in frame.dtypes.items()},
        unique_counts={str(column): int(frame[column].nunique(dropna=False)) for column in frame.columns},
        numeric_ranges=numeric_ranges,
        categorical_values=categorical_values,
        binary_distributions=binary_distributions,
        target_distribution=target_distribution,
    )
