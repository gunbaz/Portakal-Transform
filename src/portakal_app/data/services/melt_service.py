from __future__ import annotations

from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


class MeltService:
    def melt(
        self,
        dataset: DatasetHandle,
        *,
        id_column: str | None = None,
        ignore_non_numeric: bool = True,
        exclude_zeros: bool = False,
        item_name: str = "item",
        value_name: str = "value",
    ) -> DatasetHandle:
        df = dataset.dataframe

        id_vars: list[str] = []
        if id_column and id_column in df.columns:
            id_vars = [id_column]

        value_vars = [c for c in df.columns if c not in id_vars]

        if ignore_non_numeric:
            value_vars = [c for c in value_vars if df.get_column(c).dtype.is_numeric()]

        if not value_vars:
            return dataset

        melted = df.unpivot(
            on=value_vars,
            index=id_vars if id_vars else None,
            variable_name=item_name,
            value_name=value_name,
        )

        if exclude_zeros:
            try:
                melted = melted.filter(pl.col(value_name).cast(pl.Float64, strict=False) != 0.0)
            except Exception:
                pass

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-melted",
            display_name=f"{dataset.display_name} (melted)",
            dataframe=melted,
            row_count=melted.height,
            column_count=melted.width,
            domain=build_data_domain(melted),
        )
