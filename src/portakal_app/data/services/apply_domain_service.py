from __future__ import annotations

from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


class ApplyDomainService:
    def apply(
        self,
        data: DatasetHandle,
        template: DatasetHandle,
    ) -> DatasetHandle:
        template_columns = [col.name for col in template.domain.columns]
        data_columns = set(data.dataframe.columns)

        select_cols: list[str] = []
        new_series: list[pl.Series] = []

        for col_name in template_columns:
            if col_name in data_columns:
                select_cols.append(col_name)
            else:
                template_series = template.dataframe.get_column(col_name)
                null_series = pl.Series(col_name, [None] * data.row_count, dtype=template_series.dtype)
                new_series.append(null_series)

        result_df = data.dataframe.select(select_cols) if select_cols else pl.DataFrame()

        for series in new_series:
            result_df = result_df.with_columns(series)

        domain = build_data_domain(result_df)
        role_map = {col.name: col.role for col in template.domain.columns}
        from portakal_app.data.models import ColumnSchema, DataDomain
        adjusted_columns = tuple(
            ColumnSchema(
                name=col.name,
                dtype_repr=col.dtype_repr,
                logical_type=col.logical_type,
                role=role_map.get(col.name, col.role),
                nullable=col.nullable,
                null_count=col.null_count,
                unique_count_hint=col.unique_count_hint,
                sample_values=col.sample_values,
            )
            for col in domain.columns
        )
        domain = DataDomain(columns=adjusted_columns)

        return replace(
            data,
            dataset_id=f"{data.dataset_id}-transformed",
            display_name=f"{data.display_name} (transformed)",
            dataframe=result_df,
            row_count=result_df.height,
            column_count=result_df.width,
            domain=domain,
        )
