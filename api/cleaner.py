"""
Motor de limpieza de datos con Pandas y NumPy.
Depuración directa de celdas vacías, duplicados, outliers y errores tipográficos.
"""

from typing import Dict, Any, Tuple
import difflib
import numpy as np
import pandas as pd


class DataCleaner:
    """Proporciona inspección y limpieza de datos directamente con funciones nativas de Pandas."""

    @staticmethod
    def sanitize_for_json(data: Any) -> Any:
        """Convierte valores NaN e infinitos a tipos compatibles con JSON."""
        if isinstance(data, dict):
            return {k: DataCleaner.sanitize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [DataCleaner.sanitize_for_json(v) for v in data]
        elif isinstance(data, (np.integer, int)):
            return int(data)
        elif isinstance(data, (np.floating, float)):
            if np.isnan(data) or np.isinf(data):
                return None
            return float(data)
        elif pd.isna(data):
            return None
        elif isinstance(data, (pd.Timestamp, np.datetime64)):
            return str(data)
        return data

    @classmethod
    def inspect(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Inspecciona métricas básicas y estructura del dataset con Pandas."""
        total_rows, total_cols = df.shape
        duplicate_rows = int(df.duplicated().sum())
        total_missing_cells = int(df.isnull().sum().sum())
        rows_with_missing = int(df.isnull().any(axis=1).sum())

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        columns_info = []
        for col in df.columns:
            col_series = df[col]
            missing_cnt = int(col_series.isnull().sum())
            samples = col_series.dropna().head(3).tolist()

            columns_info.append({
                "name": str(col),
                "type": "numerico" if col in numeric_cols else "categorico",
                "missing_count": missing_cnt,
                "samples": [cls.sanitize_for_json(s) for s in samples],
            })

        preview_rows = df.head(50).replace({np.nan: None}).to_dict(orient="records")
        preview_sanitized = [cls.sanitize_for_json(row) for row in preview_rows]

        return {
            "total_rows": total_rows,
            "total_cols": total_cols,
            "total_missing_cells": total_missing_cells,
            "rows_with_missing": rows_with_missing,
            "duplicate_rows": duplicate_rows,
            "columns": columns_info,
            "preview": preview_sanitized,
        }

    @classmethod
    def clean(
        cls,
        df: pd.DataFrame,
        config: Dict[str, Any] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Aplica las operaciones nativas de Pandas para limpiar el dataset:
        1. df.drop(columns=...) -> Borrar columnas indicadas por el usuario
        2. df.drop_duplicates() -> Eliminar filas repetidas
        3. df.dropna() -> Eliminar celdas con valores faltantes
        4. series.str.strip() & fuzzy replace -> Corregir errores tipográficos
        5. series.quantile() -> Filtrar valores extremos (Outliers por IQR)
        """
        config = config or {}
        cleaned_df = df.copy()
        initial_rows, initial_cols = cleaned_df.shape

        # 1. Borrar columnas indicadas por el usuario
        drop_cols = [c for c in config.get("drop_columns", []) if c in cleaned_df.columns]
        if drop_cols:
            cleaned_df = cleaned_df.drop(columns=drop_cols)

        # 2. Eliminar filas repetidas (Pandas nativo)
        cleaned_df = cleaned_df.drop_duplicates()

        # 3. Eliminar celdas con valores faltantes (Pandas nativo)
        cleaned_df = cleaned_df.dropna()

        # 4. Normalizar texto y corregir errores tipográficos
        text_cols = cleaned_df.select_dtypes(include=["object", "string"]).columns
        for col in text_cols:
            # Preserva los nulos y limpia espacios
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip()

            # Fuzzy matching para unificar palabras con errores ortográficos
            val_counts = cleaned_df[col].value_counts()
            if 1 < len(val_counts) <= 300:
                values = val_counts.index.tolist()
                mapping = {}
                for i, target in enumerate(values):
                    t_lower = target.lower()
                    for other in values[i + 1:]:
                        if other in mapping:
                            continue
                        o_lower = other.lower()
                        if t_lower == o_lower or (len(t_lower) >= 3 and difflib.SequenceMatcher(None, t_lower, o_lower).ratio() >= 0.80):
                            mapping[other] = target
                if mapping:
                    cleaned_df[col] = cleaned_df[col].replace(mapping)

        # 5. Filtrar valores extremos / outliers numéricos con cuantiles IQR de Pandas
        numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
        rows_to_remove = set()
        for col in numeric_cols:
            series = cleaned_df[col].dropna()
            if len(series) >= 4:
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outliers_mask = (cleaned_df[col] < lower) | (cleaned_df[col] > upper)
                    rows_to_remove.update(cleaned_df[outliers_mask].index)

        if rows_to_remove:
            cleaned_df = cleaned_df.drop(index=list(rows_to_remove))

        # Métricas calculadas con Pandas
        final_rows, final_cols = cleaned_df.shape
        rows_removed = initial_rows - final_rows
        reduction_pct = round((rows_removed / initial_rows * 100), 1) if initial_rows > 0 else 0

        preview_rows = cleaned_df.head(100).replace({np.nan: None}).to_dict(orient="records")
        preview_sanitized = [cls.sanitize_for_json(r) for r in preview_rows]

        metrics = {
            "initial_rows": initial_rows,
            "final_rows": final_rows,
            "rows_removed": rows_removed,
            "reduction_percentage": reduction_pct,
            "initial_cols": initial_cols,
            "final_cols": final_cols,
            "remaining_missing_cells": int(cleaned_df.isnull().sum().sum()),
            "remaining_duplicate_rows": int(cleaned_df.duplicated().sum()),
        }

        return cleaned_df, {
            "metrics": metrics,
            "preview": preview_sanitized,
            "columns": cleaned_df.columns.tolist(),
        }
