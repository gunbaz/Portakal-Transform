from __future__ import annotations

from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


JOIN_TYPES = ("Left Join", "Inner Join", "Outer Join")


class MergeDataService:
    def merge(
        self,
        data: DatasetHandle,
        extra: DatasetHandle,
        *,
        left_on: list[str] | str,
        right_on: list[str] | str,
        join_type: str = "Left Join",
    ) -> DatasetHandle:
        df_left = data.dataframe
        df_right = extra.dataframe

        if isinstance(left_on, str):
            left_on = [left_on]
        if isinstance(right_on, str):
            right_on = [right_on]

        if "Row index" in left_on and "Row index" not in df_left.columns:
            df_left = df_left.with_row_index("Row index")

        if "Row index" in right_on and "Row index" not in df_right.columns:
            df_right = df_right.with_row_index("Row index")

        for col in left_on:
            if col not in df_left.columns:
                return data
        for col in right_on:
            if col not in df_right.columns:
                return data

        how_map = {
            "Left Join": "left",
            "Inner Join": "inner",
            "Outer Join": "full",
        }
        how = how_map.get(join_type, "left")

        right_cols_to_rename: dict[str, str] = {}
        for col in df_right.columns:
            if col not in right_on and col in df_left.columns:
                right_cols_to_rename[col] = f"{col}_right"
        if right_cols_to_rename:
            df_right = df_right.rename(right_cols_to_rename)

        for l_col, r_col in zip(left_on, right_on):
            if df_left[l_col].dtype != df_right[r_col].dtype:
                try:
                    df_right = df_right.with_columns(pl.col(r_col).cast(df_left[l_col].dtype, strict=False))
                except Exception:
                    df_left = df_left.with_columns(pl.col(l_col).cast(pl.Utf8))
                    df_right = df_right.with_columns(pl.col(r_col).cast(pl.Utf8))

        result = df_left.join(
            df_right,
            left_on=left_on,
            right_on=right_on,
            how=how,
            coalesce=True,
        )

        return replace(
            data,
            dataset_id=f"{data.dataset_id}-merged",
            display_name=f"{data.display_name} (merged)",
            dataframe=result,
            row_count=result.height,
            column_count=result.width,
            domain=build_data_domain(result),
        )
