"""
Core Data Cleaning Engine using Pandas and NumPy.
Handles missing values, duplicate rows, statistical outliers, and typographical errors.
"""

from typing import Dict, Any, List, Optional, Tuple
import difflib
import numpy as np
import pandas as pd


class DataCleaner:
    """Provides high-performance data inspection and cleaning pipelines with Pandas."""

    @staticmethod
    def sanitize_for_json(data: Any) -> Any:
        """Recursively converts NaN, Infinity, and NumPy types into JSON-compliant values."""
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
        """Analyzes the DataFrame to provide overview metrics, anomalies, and statistics."""
        total_rows, total_cols = df.shape
        duplicate_rows = int(df.duplicated().sum())

        missing_per_col = df.isnull().sum().to_dict()
        total_missing_cells = int(df.isnull().sum().sum())
        rows_with_missing = int(df.isnull().any(axis=1).sum())

        columns_info = []
        outliers_summary = {}
        typo_candidates_summary = {}

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        object_cols = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()

        # Numeric outlier inspection (using IQR 1.5)
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) >= 4:
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    count = int(((series < lower) | (series > upper)).sum())
                    if count > 0:
                        outliers_summary[col] = {
                            "count": count,
                            "lower_bound": round(float(lower), 3),
                            "upper_bound": round(float(upper), 3),
                            "min": round(float(series.min()), 3),
                            "max": round(float(series.max()), 3),
                        }

        # Text column typo inspection (detecting casing mismatch and near duplicates)
        for col in object_cols:
            series = df[col].dropna().astype(str)
            unique_vals = series.value_counts()
            if 1 < len(unique_vals) <= 250:
                # Find near duplicates
                sim_pairs = []
                val_list = unique_vals.index.tolist()
                for i, v1 in enumerate(val_list):
                    v1_clean = v1.strip().lower()
                    for v2 in val_list[i + 1:]:
                        v2_clean = v2.strip().lower()
                        # Case mismatch or fuzzy match
                        if v1 != v2:
                            if v1_clean == v2_clean:
                                sim_pairs.append({
                                    "original": v2,
                                    "target": v1,
                                    "similarity": 1.0,
                                    "reason": "Diferencia de mayúsculas/minúsculas"
                                })
                            else:
                                ratio = difflib.SequenceMatcher(None, v1_clean, v2_clean).ratio()
                                if ratio >= 0.82 and len(v1_clean) >= 3 and len(v2_clean) >= 3:
                                    sim_pairs.append({
                                        "original": v2,
                                        "target": v1,
                                        "similarity": round(ratio, 2),
                                        "reason": f"Similitud fonética/tipográfica ({int(ratio*100)}%)"
                                    })
                if sim_pairs:
                    typo_candidates_summary[col] = sim_pairs[:5]

        for col in df.columns:
            col_series = df[col]
            missing_cnt = int(col_series.isnull().sum())
            unique_cnt = int(col_series.nunique(dropna=True))
            dtype_str = str(col_series.dtype)

            col_type = "categorico"
            if col in numeric_cols:
                col_type = "numerico"
            elif "datetime" in dtype_str:
                col_type = "fecha"
            elif "bool" in dtype_str:
                col_type = "booleano"

            # Sample non-null values
            samples = col_series.dropna().head(3).tolist()
            samples_clean = [cls.sanitize_for_json(s) for s in samples]

            columns_info.append({
                "name": str(col),
                "type": col_type,
                "dtype": dtype_str,
                "missing_count": missing_cnt,
                "missing_pct": round((missing_cnt / total_rows * 100), 1) if total_rows > 0 else 0,
                "unique_count": unique_cnt,
                "samples": samples_clean,
                "has_outliers": col in outliers_summary,
                "has_typos": col in typo_candidates_summary,
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
            "numeric_columns": numeric_cols,
            "text_columns": object_cols,
            "outliers_summary": outliers_summary,
            "typo_candidates_summary": typo_candidates_summary,
            "preview": preview_sanitized,
        }

    @classmethod
    def clean(
        cls,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Executes data cleaning pipeline according to configuration:
        1. Fix typographical errors & string normalization
        2. Remove duplicate rows
        3. Clean missing values (dropna)
        4. Handle outliers (IQR or Z-Score: remove or clip)
        """
        cleaned_df = df.copy()
        audit_log: List[Dict[str, Any]] = []

        initial_rows, initial_cols = cleaned_df.shape
        step_index = 1

        # ==========================================
        # STEP 0: ELIMINACIÓN MANUAL DE COLUMNAS
        # ==========================================
        drop_columns = config.get("drop_columns", [])
        if drop_columns and isinstance(drop_columns, list):
            existing_to_drop = [c for c in drop_columns if c in cleaned_df.columns]
            if existing_to_drop:
                cleaned_df = cleaned_df.drop(columns=existing_to_drop)
                audit_log.append({
                    "step": step_index,
                    "category": "columnas",
                    "action": "Eliminación de columnas",
                    "detail": f"Se eliminaron las columnas: {', '.join(existing_to_drop)}",
                    "count": len(existing_to_drop),
                })
                step_index += 1

        # ==========================================
        # STEP 1: ERRORES TIPOGRÁFICOS / TOPOGRÁFICOS
        # ==========================================
        typos_config = config.get("typos", {})
        if typos_config.get("enabled", True):
            normalize_whitespace = typos_config.get("normalize_whitespace", True)
            normalize_casing = typos_config.get("normalize_casing", False)
            fuzzy_unify = typos_config.get("fuzzy_unify", True)
            similarity_threshold = float(typos_config.get("similarity_threshold", 0.85))
            target_cols = typos_config.get("columns")

            text_cols = cleaned_df.select_dtypes(include=["object", "string", "category"]).columns.tolist()
            if target_cols:
                text_cols = [c for c in text_cols if c in target_cols]

            typo_corrections_count = 0
            for col in text_cols:
                series = cleaned_df[col]
                # Whitespace cleaning
                if normalize_whitespace:
                    non_null_mask = series.notnull()
                    cleaned_df.loc[non_null_mask, col] = (
                        series[non_null_mask].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
                    )

                # Casing standardization if requested (e.g. Title Case)
                if normalize_casing:
                    non_null_mask = cleaned_df[col].notnull()
                    cleaned_df.loc[non_null_mask, col] = (
                        cleaned_df.loc[non_null_mask, col].astype(str).str.title()
                    )

                # Fuzzy typo clustering & unification
                if fuzzy_unify:
                    counts = cleaned_df[col].dropna().value_counts()
                    if 1 < len(counts) <= 400:
                        values = counts.index.tolist()
                        mapping = {}

                        for i, dominant in enumerate(values):
                            dom_clean = str(dominant).strip().lower()
                            if dominant in mapping:
                                continue

                            for other in values[i + 1:]:
                                if other in mapping:
                                    continue
                                oth_clean = str(other).strip().lower()

                                # Same word, different casing
                                if dom_clean == oth_clean and dominant != other:
                                    mapping[other] = dominant
                                    typo_corrections_count += int(counts[other])
                                    audit_log.append({
                                        "step": step_index,
                                        "category": "tipografia",
                                        "column": col,
                                        "action": "Unificación de mayúsculas/minúsculas",
                                        "detail": f"Se reemplazó '{other}' por '{dominant}' ({counts[other]} filas)",
                                    })
                                else:
                                    # Similarity calculation
                                    ratio = difflib.SequenceMatcher(None, dom_clean, oth_clean).ratio()
                                    if ratio >= similarity_threshold and len(dom_clean) >= 3 and len(oth_clean) >= 3:
                                        mapping[other] = dominant
                                        typo_corrections_count += int(counts[other])
                                        audit_log.append({
                                            "step": step_index,
                                            "category": "tipografia",
                                            "column": col,
                                            "action": "Corrección de error tipográfico",
                                            "detail": f"Se corrigió '{other}' -> '{dominant}' ({int(ratio*100)}% similitud, {counts[other]} filas)",
                                        })

                        if mapping:
                            cleaned_df[col] = cleaned_df[col].replace(mapping)

            if typo_corrections_count > 0:
                audit_log.insert(0, {
                    "step": step_index,
                    "category": "resumen",
                    "action": "Normalización de texto y tipografía",
                    "detail": f"Se corrigieron {typo_corrections_count} valores tipográficos inconsistentes en columnas de texto.",
                })
            step_index += 1

        # ==========================================
        # STEP 2: ELIMINAR FILAS REPETIDAS
        # ==========================================
        duplicates_config = config.get("duplicates", {})
        if duplicates_config.get("enabled", True):
            subset = duplicates_config.get("subset")
            keep = duplicates_config.get("keep", "first")
            if subset and not isinstance(subset, list):
                subset = None

            dup_count = int(cleaned_df.duplicated(subset=subset, keep=keep).sum())
            if dup_count > 0:
                cleaned_df = cleaned_df.drop_duplicates(subset=subset, keep=keep)
                audit_log.append({
                    "step": step_index,
                    "category": "duplicados",
                    "action": "Eliminación de filas repetidas",
                    "detail": f"Se eliminaron {dup_count} filas duplicadas (conservando '{keep}').",
                    "count": dup_count,
                })
            else:
                audit_log.append({
                    "step": step_index,
                    "category": "duplicados",
                    "action": "Verificación de duplicados",
                    "detail": "No se encontraron filas repetidas.",
                    "count": 0,
                })
            step_index += 1

        # ==========================================
        # STEP 3: ELIMINAR CELDAS FALTANTES
        # ==========================================
        missing_config = config.get("missing", {})
        if missing_config.get("enabled", True):
            mode = missing_config.get("mode", "drop_rows_any")  # drop_rows_any, drop_rows_all, drop_threshold
            threshold_pct = float(missing_config.get("threshold_pct", 50.0))
            drop_empty_columns = missing_config.get("drop_empty_columns", False)

            rows_before_missing = len(cleaned_df)

            # Drop completely empty columns if requested
            if drop_empty_columns:
                all_null_cols = cleaned_df.columns[cleaned_df.isnull().all()].tolist()
                if all_null_cols:
                    cleaned_df = cleaned_df.drop(columns=all_null_cols)
                    audit_log.append({
                        "step": step_index,
                        "category": "faltantes",
                        "action": "Eliminación de columnas 100% vacías",
                        "detail": f"Se eliminaron las columnas: {', '.join(all_null_cols)}",
                    })

            if mode == "drop_rows_any":
                # Drop rows with ANY missing value
                cleaned_df = cleaned_df.dropna(how="any")
            elif mode == "drop_rows_all":
                # Drop rows where ALL values are missing
                cleaned_df = cleaned_df.dropna(how="all")
            elif mode == "drop_threshold":
                # Keep only rows with at least N non-null values
                min_non_null = int(cleaned_df.shape[1] * (1.0 - threshold_pct / 100.0))
                cleaned_df = cleaned_df.dropna(thresh=max(1, min_non_null))

            rows_dropped = rows_before_missing - len(cleaned_df)
            audit_log.append({
                "step": step_index,
                "category": "faltantes",
                "action": "Eliminación de celdas faltantes",
                "detail": f"Se eliminaron {rows_dropped} filas con datos faltantes (modo: '{mode}').",
                "count": rows_dropped,
            })
            step_index += 1

        # ==========================================
        # STEP 4: VALORES EXTREMOS (OUTLIERS)
        # ==========================================
        outliers_config = config.get("outliers", {})
        if outliers_config.get("enabled", True) and len(cleaned_df) > 0:
            method = outliers_config.get("method", "iqr")  # 'iqr' or 'zscore'
            action = outliers_config.get("action", "remove")  # 'remove' or 'clip'
            factor = float(outliers_config.get("factor", 1.5))  # 1.5 for IQR, 3.0 for z-score
            selected_cols = outliers_config.get("columns")

            numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns.tolist()
            if selected_cols:
                numeric_cols = [c for c in numeric_cols if c in selected_cols]

            total_outliers_detected = 0
            rows_to_drop = set()

            for col in numeric_cols:
                series = cleaned_df[col].dropna()
                if len(series) < 4:
                    continue

                if method == "iqr":
                    q1 = series.quantile(0.25)
                    q3 = series.quantile(0.75)
                    iqr = q3 - q1
                    if iqr <= 0:
                        continue
                    lower = q1 - factor * iqr
                    upper = q3 + factor * iqr
                else:  # z-score
                    mean = series.mean()
                    std = series.std()
                    if std <= 0 or np.isnan(std):
                        continue
                    lower = mean - factor * std
                    upper = mean + factor * std

                outlier_mask = (cleaned_df[col] < lower) | (cleaned_df[col] > upper)
                col_outliers = int(outlier_mask.sum())

                if col_outliers > 0:
                    total_outliers_detected += col_outliers
                    if action == "remove":
                        bad_indices = cleaned_df[outlier_mask].index.tolist()
                        rows_to_drop.update(bad_indices)
                        audit_log.append({
                            "step": step_index,
                            "category": "extremos",
                            "column": col,
                            "action": f"Detección de valores extremos ({method.upper()})",
                            "detail": f"{col_outliers} valores fuera de rango [{round(lower, 2)}, {round(upper, 2)}]. Filas marcadas para eliminación.",
                            "count": col_outliers,
                        })
                    elif action == "clip":
                        cleaned_df[col] = cleaned_df[col].clip(lower=lower, upper=upper)
                        audit_log.append({
                            "step": step_index,
                            "category": "extremos",
                            "column": col,
                            "action": f"Acotamiento de valores extremos (Winsorizing {method.upper()})",
                            "detail": f"{col_outliers} valores acotados a límites [{round(lower, 2)}, {round(upper, 2)}].",
                            "count": col_outliers,
                        })

            if action == "remove" and rows_to_drop:
                rows_before = len(cleaned_df)
                cleaned_df = cleaned_df.drop(index=list(rows_to_drop))
                dropped_outliers = rows_before - len(cleaned_df)
                audit_log.append({
                    "step": step_index,
                    "category": "extremos",
                    "action": "Eliminación de filas con valores atípicos",
                    "detail": f"Se eliminaron {dropped_outliers} filas que contenían valores extremos.",
                    "count": dropped_outliers,
                })
            elif total_outliers_detected == 0:
                audit_log.append({
                    "step": step_index,
                    "category": "extremos",
                    "action": "Análisis de valores extremos",
                    "detail": "No se encontraron valores atípicos significativos en las columnas numéricas.",
                    "count": 0,
                })
            step_index += 1

        final_rows, final_cols = cleaned_df.shape
        rows_removed_total = initial_rows - final_rows
        pct_reduced = round((rows_removed_total / initial_rows * 100), 1) if initial_rows > 0 else 0

        preview_rows = cleaned_df.head(100).replace({np.nan: None}).to_dict(orient="records")
        preview_sanitized = [cls.sanitize_for_json(r) for r in preview_rows]

        metrics = {
            "initial_rows": initial_rows,
            "final_rows": final_rows,
            "rows_removed": rows_removed_total,
            "reduction_percentage": pct_reduced,
            "initial_cols": initial_cols,
            "final_cols": final_cols,
            "remaining_missing_cells": int(cleaned_df.isnull().sum().sum()),
            "remaining_duplicate_rows": int(cleaned_df.duplicated().sum()),
        }

        return cleaned_df, {
            "metrics": metrics,
            "audit_log": audit_log,
            "preview": preview_sanitized,
            "columns": cleaned_df.columns.tolist(),
        }
