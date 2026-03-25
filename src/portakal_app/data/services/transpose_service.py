from __future__ import annotations

from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


class TransposeService:
    def transpose(
        self,
        dataset: DatasetHandle,
        *,
        feature_names_from: str | None = None,
        feature_name_prefix: str = "Feature",
        auto_column_name: str = "column",
    ) -> DatasetHandle:
        df = dataset.dataframe

        if feature_names_from and feature_names_from in df.columns:
            name_series = df.get_column(feature_names_from).cast(pl.Utf8)
            names = name_series.to_list()
            df_without = df.drop(feature_names_from)
        else:
            names = None
            df_without = df

        original_col_names = df_without.columns
        transposed = df_without.transpose(include_header=True, header_name=auto_column_name)

        if names:
            new_col_names = [auto_column_name] + [str(n) if n is not None else f"row_{i}" for i, n in enumerate(names)]
            if len(new_col_names) == len(transposed.columns):
                transposed.columns = new_col_names
        else:
            new_col_names = [auto_column_name] + [
                f"{feature_name_prefix}{i + 1}" for i in range(len(transposed.columns) - 1)
            ]
            if len(new_col_names) == len(transposed.columns):
                transposed.columns = new_col_names

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-transposed",
            display_name=f"{dataset.display_name} (transposed)",
            dataframe=transposed,
            row_count=transposed.height,
            column_count=transposed.width,
            domain=build_data_domain(transposed),
        )
