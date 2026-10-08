# Customer Segmentation & Churn Pattern Analytics in European Banking

## Executive Summary

The supplied snapshot contains 10,000 customers and an observed churn rate of 20.4%. The analysis compares churn by country, age, tenure, credit score, balance, gender, product ownership, and activity. It reports association and balance exposure without making causal or revenue claims.

## Introduction

Customer retention is a relevant operating concern for retail banks. This project organizes customer-level churn patterns into interpretable portfolio and segment measures.

## Background and Context

The project brief frames churn as a source of potential lifetime-value and acquisition pressure. The supplied data does not include realized income, costs, or customer-level profitability, so those impacts cannot be quantified here.

## Problem Statement

Portfolio churn rates alone do not show how churn is distributed across customer groups or how the financial profile of churners compares with retained customers.

## Objectives

- Measure total churn and segment churn rates.
- Compare churn contribution separately from segment churn rate.
- Describe geography, demographic, financial, tenure, product, and engagement patterns.
- Quantify associated account-balance exposure and produce evidence-linked review priorities.

## Dataset Description

The analysis uses 10,000 rows and 14 supplied columns. `Exited` is the binary outcome (1 = churned, 0 = retained). `Year` is present as a constant snapshot field in the CSV but absent from the DOCX schema table; it is retained as provenance and excluded from explanatory segmentation.

## Data Quality Assessment

Missing cells: 0; duplicate rows: 0; duplicate customer identifiers beyond the first occurrence: 0. See [data_quality_report.md](data_quality_report.md) for the complete checks and findings. No records are deleted based on statistical outlier status.

## Analytical Methodology

Churn rates use churned customers divided by all customers in the relevant population. Churn contribution uses churners in the segment divided by all churners. The geographic risk index is the country churn rate divided by the portfolio churn rate. Categorical associations use chi-square tests with Cramér’s V; numeric distributions use two-sided Mann–Whitney U tests. Reported p-values use a Holm family-wise adjustment across the planned tests. Statistical significance is not evidence of causality.

## Customer Segmentation Framework

- Age: `<30` = 18–29; `30–45` = 30–45; `46–60` = 46–60; `60+` = 61+. Groups are disjoint.
- Credit score: Low / Medium / High using sample tertiles; cutoffs 608.0 and 695.0.
- Tenure: New = 0–2 years; Mid-term = 3–6 years; Long-term = 7–10 years.
- Balance: zero balance; low positive balance through 119839.69; high positive balance above that value.
- High-value proxy: positive-balance customers at or above the configured positive balance >= 75% quantile (balance threshold 139512.29). It is a high-balance screen, not a profitability classification.

## Exploratory Data Analysis

The raw snapshot contains 10,000 observations, 14 columns, 2,037 churners, and 7,963 retained customers.

## Overall Churn Analysis

Observed churn is 2,037 / 10,000 = 20.4%.

## Geographic Analysis

| segment | customer_count | churned_count | churn_rate | churn_contribution | churn_index |
| ------- | -------------- | ------------- | ---------- | ------------------ | ----------- |
| France  | 5,014          | 810           | 0.162      | 0.398              | 0.793       |
| Germany | 2,509          | 814           | 0.324      | 0.400              | 1.593       |
| Spain   | 2,477          | 413           | 0.167      | 0.203              | 0.819       |

## Demographic Analysis

| segment | customer_count | churned_count | churn_rate | churn_contribution | churn_index |
| ------- | -------------- | ------------- | ---------- | ------------------ | ----------- |
| Female  | 4,543          | 1,139         | 0.251      | 0.559              | 1.231       |
| Male    | 5,457          | 898           | 0.165      | 0.441              | 0.808       |

## Age and Tenure Analysis

| segment | customer_count | churned_count | churn_rate | churn_contribution | churn_index |
| ------- | -------------- | ------------- | ---------- | ------------------ | ----------- |
| <30     | 1,641          | 124           | 0.076      | 0.061              | 0.371       |
| 30–45   | 6,248          | 956           | 0.153      | 0.469              | 0.751       |
| 46–60   | 1,647          | 842           | 0.511      | 0.413              | 2.510       |
| 60+     | 464            | 115           | 0.248      | 0.056              | 1.217       |

## Credit Score Analysis

| segment | customer_count | churned_count | churn_rate | churn_contribution | churn_index |
| ------- | -------------- | ------------- | ---------- | ------------------ | ----------- |
| Low     | 3,363          | 724           | 0.215      | 0.355              | 1.057       |
| Medium  | 3,334          | 659           | 0.198      | 0.324              | 0.970       |
| High    | 3,303          | 654           | 0.198      | 0.321              | 0.972       |

## Financial Profile Analysis

| segment      | customer_count | churned_count | churn_rate | churn_contribution | churn_index |
| ------------ | -------------- | ------------- | ---------- | ------------------ | ----------- |
| Zero-balance | 3,617          | 500           | 0.138      | 0.245              | 0.679       |
| Low-balance  | 3,192          | 766           | 0.240      | 0.376              | 1.178       |
| High-balance | 3,191          | 771           | 0.242      | 0.378              | 1.186       |

## Engagement Analysis

| segment  | customer_count | churned_count | churn_rate | churn_contribution | churn_index |
| -------- | -------------- | ------------- | ---------- | ------------------ | ----------- |
| Inactive | 4,849          | 1,302         | 0.269      | 0.639              | 1.318       |
| Active   | 5,151          | 735           | 0.143      | 0.361              | 0.700       |

## Product Analysis

| segment | customer_count | churned_count | churn_rate | churn_contribution | churn_index |
| ------- | -------------- | ------------- | ---------- | ------------------ | ----------- |
| 1       | 5,084          | 1,409         | 0.277      | 0.692              | 1.361       |
| 2       | 4,590          | 348           | 0.076      | 0.171              | 0.372       |
| 3       | 266            | 220           | 0.827      | 0.108              | 4.060       |
| 4       | 60             | 60            | 1.000      | 0.029              | 4.909       |

## High-Value Customer Analysis

The high-balance proxy has 1,596 customers, 367 churners, and 23.0% churn. These customers represent 18.0% of churners; their churned balance exposure is 58,714,368.09.

## Balance Exposure Analysis

Churned customers held 185,588,094.63 in observed account balance, equal to 24.3% of total observed balance. This is not a lost-revenue estimate.

## KPI Framework

Portfolio churn rate = churned / total; segment churn rate = segment churned / segment customers; churn contribution = segment churned / portfolio churned; geographic risk index = country churn rate / portfolio churn rate; engagement indicator = inactive churn rate compared with active churn rate.

## Statistical Results

| variable        | test                       | n      | statistic    | p_value | effect_size | null_hypothesis                                                                 | interpretation                                                                                             | retained_n | churned_n | p_value_adjusted | significant |
| --------------- | -------------------------- | ------ | ------------ | ------- | ----------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ---------- | --------- | ---------------- | ----------- |
| Geography       | Chi-square independence    | 10,000 | 301.2553     | 0.0000  | 0.1736      | Geography and churn are independent.                                            | Evidence of association after Holm correction; this observational comparison does not establish causation. |            |           | 0.0000           | True        |
| Gender          | Chi-square independence    | 10,000 | 113.4491     | 0.0000  | 0.1065      | Gender and churn are independent.                                               | Evidence of association after Holm correction; this observational comparison does not establish causation. |            |           | 0.0000           | True        |
| IsActiveMember  | Chi-square independence    | 10,000 | 243.7604     | 0.0000  | 0.1561      | IsActiveMember and churn are independent.                                       | Evidence of association after Holm correction; this observational comparison does not establish causation. |            |           | 0.0000           | True        |
| Age             | Mann–Whitney U (two-sided) | 10,000 | 4345981.5000 | 0.0000  | 0.4641      | The Age distributions are equal for retained and churned customers.             | Evidence of association after Holm correction; this observational comparison does not establish causation. | 7963.0000  | 2037.0000 | 0.0000           | True        |
| CreditScore     | Mann–Whitney U (two-sided) | 10,000 | 8381083.0000 | 0.0199  | 0.0334      | The CreditScore distributions are equal for retained and churned customers.     | No statistically significant association detected after Holm correction at the 5% family-wise level.       | 7963.0000  | 2037.0000 | 0.0596           | False       |
| Tenure          | Mann–Whitney U (two-sided) | 10,000 | 8272055.5000 | 0.1622  | 0.0199      | The Tenure distributions are equal for retained and churned customers.          | No statistically significant association detected after Holm correction at the 5% family-wise level.       | 7963.0000  | 2037.0000 | 0.3244           | False       |
| Balance         | Mann–Whitney U (two-sided) | 10,000 | 6849444.5000 | 0.0000  | 0.1555      | The Balance distributions are equal for retained and churned customers.         | Evidence of association after Holm correction; this observational comparison does not establish causation. | 7963.0000  | 2037.0000 | 0.0000           | True        |
| EstimatedSalary | Mann–Whitney U (two-sided) | 10,000 | 7969863.0000 | 0.2271  | 0.0173      | The EstimatedSalary distributions are equal for retained and churned customers. | No statistically significant association detected after Holm correction at the 5% family-wise level.       | 7963.0000  | 2037.0000 | 0.3244           | False       |

## Key Findings

- **Germany has an elevated observed churn rate.** 814 of 2,509 customers churned (32.4%), versus 20.4% overall. This segment has a higher observed churn rate than the filtered portfolio.
- **Customers aged 46–60 have an elevated observed churn rate.** 842 of 1,647 customers churned (51.1%), versus 20.4% overall. This segment has a higher observed churn rate than the filtered portfolio.
- **Customers with 3 product(s) have an elevated observed churn rate.** 220 of 266 customers churned (82.7%), versus 20.4% overall. This segment has a higher observed churn rate than the filtered portfolio.
- **Customers in Germany aged 46–60 have an elevated observed churn rate.** 338 of 502 customers churned (67.3%), versus 20.4% overall. This geography-age combination has a higher observed churn rate than the filtered portfolio.
- **Inactive members have a higher observed churn rate than active members.** Inactive: 26.9% (n=4,849); active: 14.3% (n=5,151). Lower recorded activity co-occurs with higher churn in this snapshot.

## Business Implications

The segment comparisons can help prioritize follow-up investigation, but intervention decisions should consider customer experience, operational capacity, fairness, and outcomes from controlled retention evaluations.

## Recommendations

- Review this segment's service, product, and engagement experience before designing a targeted retention test.
- Review this segment's service, product, and engagement experience before designing a targeted retention test.
- Review this segment's service, product, and engagement experience before designing a targeted retention test.
- Review the customer journey for this combination and evaluate a targeted retention test before scaling any intervention.
- Test proactive engagement outreach and measure subsequent retention before scaling it.

## Limitations

This is a single-period snapshot without transaction history, churn timing, profitability, revenue-per-customer, service interactions, marketing exposure, or observed retention interventions. Findings are descriptive and do not establish causality or forward-looking risk.

## Conclusion

The supplied snapshot has an observed churn rate of 20.4%. Geographic, demographic, financial, engagement, and product summaries identify where churn is concentrated and where rates are elevated, subject to the sample sizes and limitations reported above.

## Technical Appendix

Generated CSV tables are in `data/outputs/`; static figures are in `reports/figures/`. Pipeline code and segmentation thresholds are centralized in the project source and configuration.
