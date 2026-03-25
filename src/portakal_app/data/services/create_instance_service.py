from __future__ import annotations

from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


class CreateInstanceService:
    def create(
        self,
        dataset: DatasetHandle,
        *,
        values: dict[str, object],
        append_to_data: bool = False,
    ) -> DatasetHandle:
        df = dataset.dataframe

        row_data: dict[str, list] = {}
        for col_name in df.columns:
            series = df.get_column(col_name)
            if col_name in values:
                val = values[col_name]
                try:
                    if series.dtype.is_numeric():
                        val = float(val) if val is not None and str(val).strip() != "" else None
                except (ValueError, TypeError):
                    val = None
                row_data[col_name] = [val]
            else:
                row_data[col_name] = [None]

        new_row = pl.DataFrame(row_data, schema={c: df.get_column(c).dtype for c in df.columns})

        if append_to_data:
            result = pl.concat([df, new_row], how="vertical_relaxed")
        else:
            result = new_row

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-instance",
            display_name=f"{dataset.display_name} (instance)",
            dataframe=result,
            row_count=result.height,
            column_count=result.width,
            domain=build_data_domain(result),
        )

    def get_defaults(self, dataset: DatasetHandle) -> dict[str, str]:
        defaults: dict[str, str] = {}
        for col in dataset.domain.columns:
            series = dataset.dataframe.get_column(col.name)
            non_null = series.drop_nulls()
            if non_null.len() == 0:
                defaults[col.name] = ""
                continue
            if series.dtype.is_numeric():
                median = non_null.median()
                defaults[col.name] = str(median) if median is not None else ""
            else:
                mode = non_null.mode()
                defaults[col.name] = str(mode[0]) if mode.len() > 0 else ""
        return defaults
