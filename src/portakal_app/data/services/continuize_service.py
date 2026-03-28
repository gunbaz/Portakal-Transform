from __future__ import annotations

from dataclasses import replace
import polars as pl
from portakal_app.data.models import DatasetHandle, build_data_domain

DISCRETE_METHODS = (
    "Use preset",
    "Keep categorical",
    "First value as base",
    "Most frequent as base",
    "One-hot encoding",
    "Remove if more than 2 values",
    "Remove",
    "Treat as ordinal",
    "Treat as normalized ordinal",
)

CONTINUOUS_METHODS = (
    "Use preset",
    "Keep as it is",
    "Standardize to μ=0, σ²=1",
    "Center to μ=0",
    "Scale to σ²=1",
    "Normalize to interval [-1, 1]",
    "Normalize to interval [0, 1]",
)

class ContinuizeService:
    def continuize(
        self,
        dataset: DatasetHandle,
        *,
        discrete_preset: str = "First value as base",
        continuous_preset: str = "Keep as it is",
        column_methods: dict[str, str] | None = None,
    ) -> DatasetHandle:
        df = dataset.dataframe
        result_series: list[pl.Series] = []
        col_methods = column_methods or {}

        for col_name in df.columns:
            series = df.get_column(col_name)
            method = col_methods.get(col_name, "Use preset")

            if series.dtype.is_numeric():
                if method == "Use preset":
                    method = continuous_preset
                result_series.extend(_transform_continuous(series, col_name, method))
            elif series.dtype == pl.Utf8 or series.dtype == pl.Categorical:
                if method == "Use preset":
                    method = discrete_preset
                result_series.extend(_transform_discrete(series, col_name, method))
            else:
                result_series.append(series)

        if not result_series:
            return replace(
                dataset,
                dataset_id=f"{dataset.dataset_id}-continuized",
                display_name=f"{dataset.display_name} (continuized)",
                dataframe=pl.DataFrame(),
                row_count=0,
                column_count=0,
                domain=build_data_domain(pl.DataFrame()),
            )

        result_df = pl.DataFrame(result_series)

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-continuized",
            display_name=f"{dataset.display_name} (continuized)",
            dataframe=result_df,
            row_count=result_df.height,
            column_count=result_df.width,
            domain=build_data_domain(result_df),
        )


def _transform_continuous(series: pl.Series, name: str, method: str) -> list[pl.Series]:
    if method == "Keep as it is" or method == "Keep as is":
        return [series]

    float_series = series.cast(pl.Float64)
    non_null = float_series.drop_nulls()

    if non_null.len() == 0:
        return [float_series]

    mean = float(non_null.mean())
    std = float(non_null.std()) if non_null.len() > 1 else 1.0
    min_val = float(non_null.min())
    max_val = float(non_null.max())

    if std == 0:
        std = 1.0
    val_range = max_val - min_val
    if val_range == 0:
        val_range = 1.0

    if method == "Standardize to μ=0, σ²=1" or method == "Standardize (mean=0, var=1)":
        return [((float_series - mean) / std).alias(name)]
    elif method == "Center to μ=0" or method == "Center (mean=0)":
        return [(float_series - mean).alias(name)]
    elif method == "Scale to σ²=1" or method == "Scale (var=1)":
        return [(float_series / std).alias(name)]
    elif method == "Normalize to interval [0, 1]" or method == "Normalize to [0, 1]":
        return [((float_series - min_val) / val_range).alias(name)]
    elif method == "Normalize to interval [-1, 1]" or method == "Normalize to [-1, 1]":
        return [((float_series - min_val) / val_range * 2 - 1).alias(name)]
    return [series]


def _transform_discrete(series: pl.Series, name: str, method: str) -> list[pl.Series]:
    if method == "Keep categorical":
        return [series]

    if method == "Remove categorical" or method == "Remove":
        return []

    str_series = series.cast(pl.Utf8).fill_null("")
    unique_vals = sorted(set(str_series.to_list()) - {""})

    if not unique_vals:
        return [series]

    if method == "Remove if more than 2 values":
        if len(unique_vals) > 2:
            return []
        # Fall back to one-hot if <= 2
        method = "First value as base"

    if method == "Treat as ordinal":
        mapping = {v: float(i) for i, v in enumerate(unique_vals)}
        values = [mapping.get(str(v), None) for v in str_series.to_list()]
        return [pl.Series(name, values, dtype=pl.Float64)]

    if method == "Treat as normalized ordinal":
        n = len(unique_vals)
        divisor = max(n - 1, 1)
        mapping = {v: float(i) / divisor for i, v in enumerate(unique_vals)}
        values = [mapping.get(str(v), None) for v in str_series.to_list()]
        return [pl.Series(name, values, dtype=pl.Float64)]

    if method == "One-hot encoding":
        result = []
        for val in unique_vals:
            col_name = f"{name}={val}"
            indicators = [1.0 if str(v) == val else 0.0 for v in str_series.to_list()]
            result.append(pl.Series(col_name, indicators, dtype=pl.Float64))
        return result

    if method == "First value as base":
        if len(unique_vals) <= 1:
            return []
        base = unique_vals[0]
        result = []
        for val in unique_vals[1:]:
            col_name = f"{name}={val}"
            indicators = [1.0 if str(v) == val else 0.0 for v in str_series.to_list()]
            result.append(pl.Series(col_name, indicators, dtype=pl.Float64))
        return result

    if method == "Most frequent as base":
        freq = {}
        for v in str_series.to_list():
            if v:
                freq[v] = freq.get(v, 0) + 1
        if not freq:
            return []
        most_freq = max(freq.keys(), key=lambda x: freq[x])
        result = []
        for val in unique_vals:
            if val == most_freq:
                continue
            col_name = f"{name}={val}"
            indicators = [1.0 if str(v) == val else 0.0 for v in str_series.to_list()]
            result.append(pl.Series(col_name, indicators, dtype=pl.Float64))
        return result

    return [series]
