from __future__ import annotations

from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


STEPS = (
    "Remove rows with missing values",
    "Remove constant features",
    "Remove features with too many missing values",
    "Normalize (0-1)",
    "Standardize (mean=0, var=1)",
)


class PreprocessService:
    def preprocess(
        self,
        dataset: DatasetHandle,
        *,
        steps: list[str],
        missing_threshold: float = 0.5,
    ) -> DatasetHandle:
        df = dataset.dataframe

        for step in steps:
            if step == "Remove rows with missing values":
                df = df.drop_nulls()
            elif step == "Remove constant features":
                cols_to_drop = []
                for col_name in df.columns:
                    if df.get_column(col_name).drop_nulls().n_unique() <= 1:
                        cols_to_drop.append(col_name)
                if cols_to_drop:
                    df = df.drop(cols_to_drop)
            elif step == "Remove features with too many missing values":
                cols_to_drop = []
                for col_name in df.columns:
                    ratio = df.get_column(col_name).null_count() / max(df.height, 1)
                    if ratio > missing_threshold:
                        cols_to_drop.append(col_name)
                if cols_to_drop:
                    df = df.drop(cols_to_drop)
            elif step == "Normalize (0-1)":
                df = _normalize(df)
            elif step == "Standardize (mean=0, var=1)":
                df = _standardize(df)

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-preprocessed",
            display_name=f"{dataset.display_name} (preprocessed)",
            dataframe=df,
            row_count=df.height,
            column_count=df.width,
            domain=build_data_domain(df),
        )


def _normalize(df: pl.DataFrame) -> pl.DataFrame:
    result = df
    for col_name in df.columns:
        series = df.get_column(col_name)
        if not series.dtype.is_numeric():
            continue
        float_s = series.cast(pl.Float64)
        min_val = float_s.min()
        max_val = float_s.max()
        if min_val is None or max_val is None or min_val == max_val:
            continue
        result = result.with_columns(
            ((pl.col(col_name).cast(pl.Float64) - min_val) / (max_val - min_val)).alias(col_name)
        )
    return result


def _standardize(df: pl.DataFrame) -> pl.DataFrame:
    result = df
    for col_name in df.columns:
        series = df.get_column(col_name)
        if not series.dtype.is_numeric():
            continue
        float_s = series.cast(pl.Float64)
        mean = float_s.mean()
        std = float_s.std()
        if mean is None or std is None or std == 0:
            continue
        result = result.with_columns(
            ((pl.col(col_name).cast(pl.Float64) - mean) / std).alias(col_name)
        )
    return result
