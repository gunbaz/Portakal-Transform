from __future__ import annotations

import random
from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


class ImputeService:
    def impute(
        self,
        dataset: DatasetHandle,
        *,
        default_method: str = "Average/Most frequent",
        default_fixed_value: str = "0",
        seed: int | None = None,
        column_methods: dict[str, dict[str, str]] | None = None,
    ) -> DatasetHandle:
        df = dataset.dataframe
        rng = random.Random(seed)
        col_methods = column_methods or {}

        # Handle global row drop (if drop happens, do it first or let it be per-column if needed?
        # Actually in Orange, "Remove instances with unknown values" is a valid method.
        # If it's a default method AND there are any columns using it, we drop rows.
        # If a column specifically overrides to "Remove instances", we drop rows where THAT column is null.
        
        result = df
        
        cols_to_drop_for = []
        for col_name in df.columns:
            method_info = col_methods.get(col_name)
            if method_info is not None:
                method = method_info.get("method", default_method)
            else:
                method = default_method
                
            if method == "Remove instances with unknown values":
                cols_to_drop_for.append(col_name)
                
        if cols_to_drop_for:
            result = result.drop_nulls(subset=cols_to_drop_for)

        for col_name in result.columns:
            series = result.get_column(col_name)
            if series.null_count() == 0:
                continue

            method_info = col_methods.get(col_name, {})
            method = method_info.get("method", default_method)
            fixed_value = method_info.get("fixed_value", default_fixed_value)

            if method == "Don't impute" or method == "Remove instances with unknown values":
                continue

            if method == "Average/Most frequent":
                if series.dtype.is_numeric():
                    fill_val = series.mean()
                    if fill_val is not None:
                        result = result.with_columns(pl.col(col_name).fill_null(fill_val))
                else:
                    mode_val = series.drop_nulls().mode()
                    if mode_val.len() > 0:
                        result = result.with_columns(pl.col(col_name).fill_null(mode_val[0]))
            elif method == "Fixed values":
                if series.dtype.is_numeric():
                    try:
                        result = result.with_columns(pl.col(col_name).fill_null(float(fixed_value)))
                    except ValueError:
                        pass
                else:
                    result = result.with_columns(pl.col(col_name).fill_null(fixed_value))
            elif method == "Random values":
                non_null = series.drop_nulls().to_list()
                if non_null:
                    values = series.to_list()
                    for i, v in enumerate(values):
                        if v is None:
                            values[i] = rng.choice(non_null)
                    result = result.with_columns(pl.Series(col_name, values, dtype=series.dtype))
            elif method == "As a distinct value":
                if series.dtype == pl.Utf8 or series.dtype == pl.Categorical:
                    # Missing treated as distinct value "N/A"
                    result = result.with_columns(pl.col(col_name).cast(pl.Utf8).fill_null("N/A").cast(series.dtype))
                # For numeric, there's no native "distinct value" so we skip or use a magic number. Skipped.

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-imputed",
            display_name=f"{dataset.display_name} (imputed)",
            dataframe=result,
            row_count=result.height,
            column_count=result.width,
            domain=build_data_domain(result),
        )

