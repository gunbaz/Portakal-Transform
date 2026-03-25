from __future__ import annotations

import random
from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


METHODS = (
    "Leave as is",
    "Average/Most frequent",
    "Fixed value",
    "Random",
    "Drop rows with missing",
)


class ImputeService:
    def impute(
        self,
        dataset: DatasetHandle,
        *,
        method: str = "Average/Most frequent",
        fixed_value: str = "0",
        seed: int | None = None,
    ) -> DatasetHandle:
        df = dataset.dataframe
        rng = random.Random(seed)

        if method == "Leave as is":
            return dataset

        if method == "Drop rows with missing":
            result = df.drop_nulls()
            return replace(
                dataset,
                dataset_id=f"{dataset.dataset_id}-imputed",
                display_name=f"{dataset.display_name} (imputed)",
                dataframe=result,
                row_count=result.height,
                domain=build_data_domain(result),
            )

        result = df
        for col_name in df.columns:
            series = df.get_column(col_name)
            if series.null_count() == 0:
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
            elif method == "Fixed value":
                if series.dtype.is_numeric():
                    try:
                        result = result.with_columns(pl.col(col_name).fill_null(float(fixed_value)))
                    except ValueError:
                        pass
                else:
                    result = result.with_columns(pl.col(col_name).fill_null(fixed_value))
            elif method == "Random":
                non_null = series.drop_nulls().to_list()
                if non_null:
                    values = series.to_list()
                    for i, v in enumerate(values):
                        if v is None:
                            values[i] = rng.choice(non_null)
                    result = result.with_columns(pl.Series(col_name, values, dtype=series.dtype))

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-imputed",
            display_name=f"{dataset.display_name} (imputed)",
            dataframe=result,
            row_count=result.height,
            domain=build_data_domain(result),
        )
