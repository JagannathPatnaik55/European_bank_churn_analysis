from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Year": [2025] * 8,
            "CustomerId": range(1, 9),
            "Surname": ["A"] * 8,
            "CreditScore": [500, 550, 600, 650, 700, 750, 800, 850],
            "Geography": ["France", "France", "Germany", "Germany", "Spain", "Spain", "France", "Germany"],
            "Gender": ["Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male"],
            "Age": [25, 40, 50, 60, 61, 29, 45, 70],
            "Tenure": [0, 2, 3, 6, 7, 10, 5, 1],
            "Balance": [0.0, 100.0, 200.0, 300.0, 400.0, 0.0, 500.0, 600.0],
            "NumOfProducts": [1, 2, 3, 1, 2, 3, 1, 2],
            "HasCrCard": [1, 0, 1, 0, 1, 0, 1, 0],
            "IsActiveMember": [1, 1, 0, 0, 1, 0, 1, 0],
            "EstimatedSalary": [1000.0, 2000.0, 3000.0, 4000.0, 5000.0, 6000.0, 7000.0, 8000.0],
            "Exited": [0, 1, 1, 0, 1, 0, 0, 1],
        }
    )
