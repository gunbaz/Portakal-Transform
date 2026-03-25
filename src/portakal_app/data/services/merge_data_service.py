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
        left_on: str,
        right_on: str,
        join_type: str = "Left Join",
    ) -> DatasetHandle:
        df_left = data.dataframe
        df_right = extra.dataframe

        if left_on not in df_left.columns or right_on not in df_right.columns:
            return data

        how_map = {
            "Left Join": "left",
            "Inner Join": "inner",
            "Outer Join": "full",
        }
        how = how_map.get(join_type, "left")

        right_cols_to_rename: dict[str, str] = {}
        for col in df_right.columns:
            if col != right_on and col in df_left.columns:
                right_cols_to_rename[col] = f"{col}_right"
        if right_cols_to_rename:
            df_right = df_right.rename(right_cols_to_rename)

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
