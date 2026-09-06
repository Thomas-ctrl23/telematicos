"""
Unit tests for Pandas DataCleaner and FastAPI endpoints.
"""

import io
import pandas as pd
import numpy as np
from api.cleaner import DataCleaner


def test_missing_values_removal():
    data = {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", None, "David", "Eve"],
        "age": [25, np.nan, 35, 40, 29],
        "city": ["Madrid", "Barcelona", "Valencia", None, "Sevilla"],
    }
    df = pd.DataFrame(data)
    cleaned, res = DataCleaner.clean(df, {"missing": {"enabled": True, "mode": "drop_rows_any"}})
    
    # Rows with nulls (index 1, 2, 3) must be dropped
    assert len(cleaned) == 2
    assert cleaned.isnull().sum().sum() == 0
    assert res["metrics"]["rows_removed"] == 3
    print("[PASS] Missing values test passed.")


def test_duplicate_rows_removal():
    data = {
        "id": [1, 2, 2, 3, 3, 3],
        "category": ["A", "B", "B", "C", "C", "C"],
        "score": [10, 20, 20, 30, 30, 30],
    }
    df = pd.DataFrame(data)
    cleaned, res = DataCleaner.clean(df, {"duplicates": {"enabled": True}})
    
    assert len(cleaned) == 3
    assert int(cleaned.duplicated().sum()) == 0
    assert res["metrics"]["rows_removed"] == 3
    print("[PASS] Duplicate rows test passed.")


def test_outliers_handling():
    # Regular values around 50, with two extreme outliers: 9999 and -500
    values = [48, 50, 52, 49, 51, 50, 47, 53, 50, 52, 9999, -500]
    df = pd.DataFrame({"metric": values})

    # Test Outlier Removal (with duplicates disabled to isolate outliers)
    cleaned_rem, res_rem = DataCleaner.clean(
        df,
        {
            "duplicates": {"enabled": False},
            "outliers": {"enabled": True, "method": "iqr", "action": "remove", "factor": 1.5}
        }
    )
    assert len(cleaned_rem) == 10
    assert 9999 not in cleaned_rem["metric"].values
    assert -500 not in cleaned_rem["metric"].values

    # Test Outlier Clipping (Winsorizing)
    cleaned_clip, res_clip = DataCleaner.clean(
        df,
        {
            "duplicates": {"enabled": False},
            "outliers": {"enabled": True, "method": "iqr", "action": "clip", "factor": 1.5}
        }
    )
    assert len(cleaned_clip) == 12
    assert cleaned_clip["metric"].max() < 100
    assert cleaned_clip["metric"].min() > 0
    print("[PASS] Outliers handling test passed.")


def test_typographical_errors():
    data = {
        "ciudad": ["Madrid", "Madird", "Madrid", "madrid", "Barcelona", "Barelona", "Valencia", "  Valencia  "]
    }
    df = pd.DataFrame(data)
    cleaned, res = DataCleaner.clean(
        df,
        {
            "typos": {
                "enabled": True,
                "normalize_whitespace": True,
                "fuzzy_unify": True,
                "similarity_threshold": 0.80
            }
        }
    )
    
    ciudades = cleaned["ciudad"].unique().tolist()
    # 'Madird' and 'madrid' should have been unified into 'Madrid'
    assert "Madird" not in ciudades
    # 'Barelona' should be unified into 'Barcelona'
    assert "Barelona" not in ciudades
    # '  Valencia  ' trimmed to 'Valencia'
    assert "  Valencia  " not in ciudades
    print("[PASS] Typographical errors test passed.")


if __name__ == "__main__":
    test_missing_values_removal()
    test_duplicate_rows_removal()
    test_outliers_handling()
    test_typographical_errors()
    print("All cleaner tests passed successfully!")
