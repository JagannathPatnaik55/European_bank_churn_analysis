# Data Quality Report

- Rows: 10,000
- Columns: 14
- Duplicate rows: 0
- Duplicate CustomerId values: 0
- Validation status: PASS WITH NOTES

## Schema and missing values

| Column | Type | Unique values | Missing |
|---|---|---:|---:|
| Year | int64 | 1 | 0 |
| CustomerId | int64 | 10,000 | 0 |
| Surname | object | 2,932 | 0 |
| CreditScore | int64 | 460 | 0 |
| Geography | object | 3 | 0 |
| Gender | object | 2 | 0 |
| Age | int64 | 70 | 0 |
| Tenure | int64 | 11 | 0 |
| Balance | float64 | 6,382 | 0 |
| NumOfProducts | int64 | 4 | 0 |
| HasCrCard | int64 | 2 | 0 |
| IsActiveMember | int64 | 2 | 0 |
| EstimatedSalary | float64 | 9,999 | 0 |
| Exited | int64 | 2 | 0 |

## Numeric ranges

| Column | Minimum | Maximum |
|---|---:|---:|
| CreditScore | 350.00 | 850.00 |
| Age | 18.00 | 92.00 |
| Tenure | 0.00 | 10.00 |
| Balance | 0.00 | 250,898.09 |
| NumOfProducts | 1.00 | 4.00 |
| EstimatedSalary | 11.58 | 199,992.48 |

## Categorical values

- **Geography values:** France, Germany, Spain
- **Gender values:** Female, Male

## Binary-field distributions

| Field | Values and counts |
|---|---|
| HasCrCard | 0: 2,945, 1: 7,055 |
| IsActiveMember | 0: 4,849, 1: 5,151 |
| Exited | 0: 7,963, 1: 2,037 |

## Findings

- **INFO — statistical_outlier:** CreditScore has values outside the 1.5×IQR fences; in-range observations are retained. (15)
- **INFO — statistical_outlier:** Age has values outside the 1.5×IQR fences; in-range observations are retained. (359)
- **INFO — statistical_outlier:** NumOfProducts has values outside the 1.5×IQR fences; in-range observations are retained. (60)
- **INFO — constant_year:** Year is constant in this file and is treated as snapshot provenance, not an explanatory feature. (1)

## Checks performed

Required schema, missing cells, exact duplicate rows, CustomerId uniqueness, geography/gender domains, binary values, and numeric ranges were checked. The target is expected to use 0 = retained and 1 = churned.

## Handling rule

Validation reports suspicious or unusual observations; it does not delete records. Statistical outliers within valid ranges are retained.

## Target distribution

| Exited | Customers |
|---:|---:|
| 0 | 7,963 |
| 1 | 2,037 |
