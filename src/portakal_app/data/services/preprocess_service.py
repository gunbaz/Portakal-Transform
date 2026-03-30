from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Any

import polars as pl
from portakal_app.data.models import DatasetHandle, build_data_domain

@dataclass
class PreprocessStep:
    name: str
    params: dict[str, Any]

class PreprocessService:
    def preprocess(
        self,
        dataset: DatasetHandle,
        *,
        steps: list[PreprocessStep],
        missing_threshold: float = 0.5, # Kept for backward compat but unused if empty steps
    ) -> DatasetHandle:
        df = dataset.dataframe
        
        for step in steps:
            # Legacy simple mode support for old saved templates
            if isinstance(step, str):
                step = PreprocessStep(name=step, params={})

            if step.name == "Normalize (0-1)":
                df = _normalize(df, method="Normalize to [0, 1]")
            elif step.name == "Standardize (mean=0, var=1)":
                df = _normalize(df, method="Standardize to μ=0, σ²=1")
            elif step.name == "Remove rows with missing values":
                df = df.drop_nulls()
            elif step.name == "Remove constant features":
                cols = [c for c in df.columns if df.get_column(c).drop_nulls().n_unique() <= 1]
                if cols:
                    df = df.drop(cols)
            elif step.name == "Remove features with too many missing values":
                cols = [c for c in df.columns if df.get_column(c).null_count() / max(df.height, 1) > missing_threshold]
                if cols:
                    df = df.drop(cols)

            # Modern Steps
            elif step.name == "Normalize Features":
                method = step.params.get("method", "Standardize to μ=0, σ²=1")
                df = _normalize(df, method=method)
                
            elif step.name == "Impute Missing Values":
                method = step.params.get("method", "Average/Most frequent")
                if method == "Remove rows with missing values":
                    df = df.drop_nulls()
                elif method == "Average/Most frequent":
                    df = _impute_average(df)
                elif method == "Replace with random value":
                    # Simple stub for replacement: fill with 0/empty for now
                    df = df.fill_null(strategy="backward").fill_null(strategy="forward")

            elif step.name == "Continuize Discrete Variables":
                df = _continuize(df, method=step.params.get("method", "One feature per value"))

            elif step.name == "Select Relevant Features":
                # Stub implementation: Select top K features randomly or by variance
                k = step.params.get("k", 10)
                strategy = step.params.get("strategy", "Fixed")
                if strategy != "Fixed":
                    k = int(max(df.width * float(k) / 100, 1))
                k = min(int(k), df.width)
                if k < df.width:
                    df = df.select(df.columns[:k])
                    
            elif step.name == "Select Random Features":
                k = step.params.get("k", 10)
                strategy = step.params.get("strategy", "Fixed")
                if strategy != "Fixed":
                    k = int(max(df.width * float(k) / 100, 1))
                k = min(int(k), df.width)
                if k < df.width:
                    import random
                    cols = random.sample(df.columns, k)
                    df = df.select(cols)
                    
            elif step.name == "Remove Sparse Features":
                use_fixed = step.params.get("useFixedThreshold", False)
                if use_fixed:
                    threshold = step.params.get("fixedThresh", 50)
                else:
                    threshold = df.height * float(step.params.get("percThresh", 5)) / 100
                
                filter0 = step.params.get("filter0", 0)
                cols_to_drop = []
                for c in df.columns:
                    col = df.get_column(c)
                    count = col.null_count() if filter0 == 0 else (col == 0).sum()
                    if count >= threshold:
                        cols_to_drop.append(c)
                if cols_to_drop:
                    df = df.drop(cols_to_drop)

            elif step.name == "Randomize":
                # Shuffle rows or randomize
                if step.params.get("classes", True):
                    df = df.sample(fraction=1.0, shuffle=True)

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-preprocessed",
            display_name=f"{dataset.display_name} (preprocessed)",
            dataframe=df,
            row_count=df.height,
            column_count=df.width,
            domain=build_data_domain(df, source_domain=dataset.domain),
        )

def _continuize(df: pl.DataFrame, method: str) -> pl.DataFrame:
    if method == "Remove categorical features" or method == "Remove non-binary features":
        cols = [c for c in df.columns if df.get_column(c).dtype == pl.Utf8 or df.get_column(c).dtype == pl.Categorical]
        return df.drop(cols) if cols else df
    elif method == "One feature per value":
        return df.to_dummies()
    elif method == "Treat as ordinal":
        res = df
        for col_name in df.columns:
            series = df.get_column(col_name)
            if series.dtype == pl.Utf8 or series.dtype == pl.Categorical:
                res = res.with_columns(series.cast(pl.Categorical).to_physical().alias(col_name))
        return res
    return df

def _impute_average(df: pl.DataFrame) -> pl.DataFrame:
    res = df
    for col_name in df.columns:
        series = df.get_column(col_name)
        if series.dtype.is_numeric():
            mean = series.mean()
            if mean is not None:
                res = res.with_columns(series.fill_null(mean).alias(col_name))
        else:
            mode_s = series.mode()
            if mode_s.len() > 0:
                res = res.with_columns(series.fill_null(mode_s[0]).alias(col_name))
    return res

def _normalize(df: pl.DataFrame, method: str) -> pl.DataFrame:
    result = df
    for col_name in df.columns:
        series = df.get_column(col_name)
        if not series.dtype.is_numeric():
            continue
        float_s = series.cast(pl.Float64)
        if "Normalize" in method:
            min_val = float_s.min()
            max_val = float_s.max()
            if min_val is None or max_val is None or min_val == max_val:
                continue
            expr = (pl.col(col_name).cast(pl.Float64) - min_val) / (max_val - min_val)
            if "[-1, 1]" in method:
                expr = expr * 2 - 1
            result = result.with_columns(expr.alias(col_name))
        elif "Standardize" in method or "Scale" in method or "Center" in method:
            mean = float_s.mean() if ("Standardize" in method or "Center" in method) else 0.0
            std = float_s.std() if ("Standardize" in method or "Scale" in method) else 1.0
            if mean is None or std is None or std == 0:
                continue
            expr = (pl.col(col_name).cast(pl.Float64) - mean) / std
            result = result.with_columns(expr.alias(col_name))
    return result

