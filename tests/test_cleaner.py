"""
Unit tests for Pandas DataCleaner.
"""

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
    cleaned, res = DataCleaner.clean(df)
    
    # Rows with nulls must be dropped
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
    cleaned, res = DataCleaner.clean(df)
    
    assert len(cleaned) == 3
    assert int(cleaned.duplicated().sum()) == 0
    assert res["metrics"]["rows_removed"] == 3
    print("[PASS] Duplicate rows test passed.")


def test_outliers_handling():
    # Regular values with two extreme outliers: 9999 and -500
    values = [48, 50, 52, 49, 51, 55, 47, 53, 54, 56, 9999, -500]
    df = pd.DataFrame({"id": list(range(12)), "metric": values})

    cleaned, res = DataCleaner.clean(df)
    assert 9999 not in cleaned["metric"].values
    assert -500 not in cleaned["metric"].values
    print("[PASS] Outliers handling test passed.")


def test_typographical_errors():
    data = {
        "id": list(range(8)),
        "ciudad": ["Madrid", "Madird", "Madrid", "madrid", "Barcelona", "Barelona", "Valencia", "  Valencia  "]
    }
    df = pd.DataFrame(data)
    cleaned, res = DataCleaner.clean(df)
    
    ciudades = cleaned["ciudad"].unique().tolist()
    assert "Madird" not in ciudades
    assert "Barelona" not in ciudades
    assert "  Valencia  " not in ciudades
    print("[PASS] Typographical errors test passed.")


def test_column_deletion():
    data = {
        "id": [1, 2, 3],
        "nombre": ["A", "B", "C"],
        "edad": [20, 25, 30]
    }
    df = pd.DataFrame(data)
    cleaned, res = DataCleaner.clean(df, config={"drop_columns": ["edad"]})
    assert "edad" not in cleaned.columns
    assert "nombre" in cleaned.columns
    print("[PASS] Column deletion test passed.")


if __name__ == "__main__":
    test_missing_values_removal()
    test_duplicate_rows_removal()
    test_outliers_handling()
    test_typographical_errors()
    test_column_deletion()
    print("All cleaner tests passed successfully!")
