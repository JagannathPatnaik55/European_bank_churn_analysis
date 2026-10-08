# Customer Segmentation & Churn Pattern Analytics in European Banking

A reproducible, local Python analytics project for understanding observed customer churn across geography, demographics, tenure, balances, product ownership, and engagement. The project combines a data-quality pipeline, transparent segmentation, statistical summaries, generated reports and figures, and a seven-view Streamlit dashboard.

## Business problem and objectives

Retail banks need more than a single churn percentage to understand which customer groups merit closer review. This project measures churn rates and churn contribution by segment, compares churned and retained customer profiles, quantifies account-balance exposure associated with churn, and turns sufficiently large differences into evidence-linked investigation priorities.

The analysis answers the questions in the project brief: portfolio churn; geography, age, tenure, credit-score, balance, gender, product and activity patterns; geography-by-age interactions; high-balance customer churn; and financial exposure. It describes observed associations. It does not estimate causal effects or future churn probabilities.

## Dataset

The supplied `European_Bank.csv` contains 10,000 rows and 14 columns. It has no missing cells, exact duplicate rows, or duplicate `CustomerId` values. The target `Exited` has 2,037 churners and 7,963 retained customers, for an overall rate of 20.37%. The data also includes `Year=2025` on every row; that field is retained as snapshot provenance and excluded from explanatory analysis. It is not listed in the schema table in `Project.docx`.

`Surname` is kept only in the untouched raw copy and removed from the processed analytical dataset. `CustomerId` is retained as a reference key but is not used as an explanatory feature. The dashboard’s high-balance detail table omits surname.

### Segmentation definitions

| Dimension | Rule |
|---|---|
| Age | `<30` = 18–29; `30–45`; `46–60`; `60+` = 61 and older. The exact age 60 is assigned to `46–60` so the groups do not overlap. |
| Credit score | Low / Medium / High based on observed sample tertiles. The run-specific cutoffs are saved in `data/outputs/segmentation_definitions.json`. |
| Tenure | New = 0–2 years; Mid-term = 3–6; Long-term = 7–10. |
| Balance | Zero balance; low positive balance through the positive-balance median; high positive balance above that median. |
| High-value proxy | Positive-balance customers at or above the 75th percentile of positive balance. This is a high-balance screen, not a profitability or lifetime-value measure. |

All segment summaries report both churn rate and contribution to portfolio churn. They answer different questions: the rate is the share of a segment that churned; contribution is the share of all churners represented by that segment.

## Project structure

```text
data/
  raw/European_Bank.csv              # untouched input copy
  processed/cleaned_dataset.csv     # engineered data, surname removed
  outputs/                           # summary CSVs, KPIs, definitions, tests
dashboard/
  app.py                             # Streamlit UI and page views
  components.py                      # shared filters and chart helpers
  styles.css
notebooks/
  01_eda_and_analysis.ipynb          # walkthrough using the project modules
reports/
  research_paper.md
  executive_summary.md
  data_quality_report.md
  figures/                           # generated PNG charts
scripts/
  run_pipeline.py
  generate_reports.py
  generate_figures.py
src/                                 # reusable ingestion, analysis, KPI, and report code
tests/                               # deterministic pytest coverage
config.yaml
requirements.txt
run_project.py
```

## Technology

Python 3.11 or newer; pandas, NumPy, SciPy, Matplotlib, Plotly, Streamlit, PyYAML, and pytest. No external services or network calls are made by the application.

## Setup

Run these commands from the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The project already includes a copy of the supplied source CSV at `data/raw/European_Bank.csv`. To use a different compatible file, replace that file while preserving the original separately.

## Run the project

Generate the processed dataset, analytical CSVs, figures, and all three Markdown reports:

```powershell
python scripts/run_pipeline.py
```

Start the dashboard:

```powershell
streamlit run dashboard/app.py
```

The sidebar includes seven views: Executive Overview, Geographic Analytics, Demographic & Tenure, Financial & Engagement, High-Value Explorer, Segment Drill-down, and Insights & Recommendations. All views respond to the global filters. **Reset filters** restores the full population; **Refresh source data** clears the cached data and reloads the CSV. Empty selections show a readable message.

Run the tests:

```powershell
python -m pytest
```

Regenerate the figures alone or the report bundle and its supporting analysis:

```powershell
python scripts/generate_figures.py
python scripts/generate_reports.py
```

`run_project.py` is a shortcut for the full pipeline:

```powershell
python run_project.py
```

## KPI definitions

- **Overall churn rate:** churned customers divided by all customers.
- **Segment churn rate:** churned customers in the segment divided by customers in that segment.
- **Churn contribution:** segment churners divided by all churners.
- **Geographic risk index:** country churn rate divided by the filtered portfolio rate. Above 1 means above-portfolio observed churn.
- **High-value churn rate:** churned customers in the high-balance proxy divided by customers in that proxy.
- **High-value churn ratio:** high-balance proxy churners divided by all churners.
- **Engagement churn indicator:** inactive-member churn rate compared with active-member churn rate.
- **Balance exposure:** sum of account balances for churned customers; this is not revenue, profit, or an amount known to be lost.

Categorical associations use chi-square tests and Cramér’s V; numeric comparisons use two-sided Mann–Whitney U tests. P-values are adjusted with Holm’s family-wise procedure across the planned tests. Results remain observational and do not establish causation.

## Actual data findings

The current source snapshot has a 20.37% overall churn rate. Germany’s observed churn rate is 32.44%, compared with 16.15% in France and 16.67% in Spain. Customers aged 46–60 have a 51.12% churn rate in this file (1,647 customers). The product-count-3 group has an 82.71% rate (266 customers); the 4-product group has 60 customers and is reported with its small sample size. Inactive members have a 26.85% rate versus 14.27% among active members.

The high-balance proxy contains 1,596 customers; 367 churned (22.99%), representing 18.02% of churners. Those churners held 58,714,368.09 in observed balance. Across all churners, the balance exposure is 185,588,094.63, or 24.26% of observed portfolio balance. These are balances, not revenue losses.

Automated recommendations are suppressed unless the segment has at least 100 customers and a churn rate at least five percentage points above the applicable portfolio rate. The generated reports and dashboard tables contain the complete calculations and caveats.

## Known limitations and assumptions

- This is a single-period snapshot; it contains no churn timeline, transactions, service interactions, marketing history, or retention interventions.
- Revenue, cost, margin, and customer lifetime value are absent. Balance exposure must not be called revenue risk.
- The high-value label is a transparent balance-based proxy, not a complete value score.
- Credit-score tertiles are dataset-relative and may change when the source population changes.
- Age `60+` means age 61 or older because the brief also defines `46–60`; this explicit boundary avoids overlapping bins.
- No predictive model is included. The brief makes prediction optional, and the project focuses on required descriptive analytics.
- Tests are deterministic and use small synthetic customer frames. They check analysis rules, data handling, and output generation; they do not certify a business retention intervention.

## Expected outputs

The pipeline writes `cleaned_dataset.csv`, `overall_kpis.csv`, segment and geography/age summaries, financial profiles and exposure, engagement KPIs, high-value analysis, statistical test results, data-quality summary, segmentation definitions, and evidence-linked key insights under `data/outputs/`. Reports are written under `reports/`; ten PNG figures are written under `reports/figures/`.
