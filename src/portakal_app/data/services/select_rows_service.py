from __future__ import annotations

from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


OPERATORS_NUMERIC = ("=", "!=", "<", "<=", ">", ">=", "is defined", "is not defined")
OPERATORS_STRING = ("equals", "not equals", "contains", "does not contain", "starts with", "ends with", "is defined", "is not defined")
OPERATORS_CATEGORICAL = ("is", "is not", "is defined", "is not defined")


class SelectRowsService:
    def filter_rows(
        self,
        dataset: DatasetHandle,
        *,
        conditions: list[tuple[str, str, str]],
    ) -> tuple[DatasetHandle | None, DatasetHandle | None]:
        df = dataset.dataframe

        if not conditions:
            return dataset, None

        mask = pl.Series("mask", [True] * df.height)
        for col_name, operator, value in conditions:
            if col_name not in df.columns:
                continue
            col_mask = _apply_condition(df, col_name, operator, value)
            mask = mask & col_mask

        matching_df = df.filter(mask)
        non_matching_df = df.filter(~mask)

        matching = None
        if matching_df.height > 0:
            matching = replace(
                dataset,
                dataset_id=f"{dataset.dataset_id}-matching",
                display_name=f"{dataset.display_name} (matching)",
                dataframe=matching_df,
                row_count=matching_df.height,
                domain=build_data_domain(matching_df),
            )

        non_matching = None
        if non_matching_df.height > 0:
            non_matching = replace(
                dataset,
                dataset_id=f"{dataset.dataset_id}-unmatched",
                display_name=f"{dataset.display_name} (unmatched)",
                dataframe=non_matching_df,
                row_count=non_matching_df.height,
                domain=build_data_domain(non_matching_df),
            )

        return matching, non_matching


def _apply_condition(df: pl.DataFrame, col_name: str, operator: str, value: str) -> pl.Series:
    series = df.get_column(col_name)
    n = df.height

    if operator == "is defined":
        return series.is_not_null()
    if operator == "is not defined":
        return series.is_null()

    if series.dtype.is_numeric():
        try:
            num_val = float(value)
        except (ValueError, TypeError):
            return pl.Series("m", [True] * n)
        float_series = series.cast(pl.Float64, strict=False)
        if operator == "=":
            return float_series == num_val
        if operator == "!=":
            return float_series != num_val
        if operator == "<":
            return float_series < num_val
        if operator == "<=":
            return float_series <= num_val
        if operator == ">":
            return float_series > num_val
        if operator == ">=":
            return float_series >= num_val

    str_series = series.cast(pl.Utf8, strict=False).fill_null("")
    if operator in ("equals", "is", "="):
        return str_series == value
    if operator in ("not equals", "is not", "!="):
        return str_series != value
    if operator == "contains":
        return str_series.str.contains(value, literal=True)
    if operator == "does not contain":
        return ~str_series.str.contains(value, literal=True)
    if operator == "starts with":
        return str_series.str.starts_with(value)
    if operator == "ends with":
        return str_series.str.ends_with(value)

    return pl.Series("m", [True] * n)
