from __future__ import annotations

import re
from dataclasses import replace

import polars as pl

from portakal_app.data.models import ColumnSchema, DataDomain, DatasetHandle, build_data_domain


class CreateClassService:
    def create_class(
        self,
        dataset: DatasetHandle,
        *,
        source_column: str,
        rules: list[tuple[str, str]],
        class_name: str = "class",
        case_sensitive: bool = False,
        use_regex: bool = False,
        match_beginning: bool = False,
    ) -> DatasetHandle:
        df = dataset.dataframe

        if source_column not in df.columns:
            return dataset

        source = df.get_column(source_column).cast(pl.Utf8).fill_null("")
        values = source.to_list()
        class_values: list[str | None] = [None] * len(values)

        for label, pattern in rules:
            for i, val in enumerate(values):
                if class_values[i] is not None:
                    continue
                if _matches(val, pattern, case_sensitive, use_regex, match_beginning):
                    class_values[i] = label

        for i, v in enumerate(class_values):
            if v is None:
                class_values[i] = "Other"

        result_df = df.with_columns(pl.Series(class_name, class_values, dtype=pl.Utf8))

        domain = build_data_domain(result_df)
        new_columns = list(domain.columns)
        for idx, col in enumerate(new_columns):
            if col.name == class_name:
                new_columns[idx] = ColumnSchema(
                    name=col.name,
                    dtype_repr=col.dtype_repr,
                    logical_type="categorical",
                    role="target",
                    nullable=col.nullable,
                    null_count=col.null_count,
                    unique_count_hint=col.unique_count_hint,
                    sample_values=col.sample_values,
                )

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-classed",
            display_name=f"{dataset.display_name} (class created)",
            dataframe=result_df,
            row_count=result_df.height,
            column_count=result_df.width,
            domain=DataDomain(columns=tuple(new_columns)),
        )


def _matches(value: str, pattern: str, case_sensitive: bool, use_regex: bool, match_beginning: bool) -> bool:
    if not case_sensitive:
        value = value.lower()
        pattern = pattern.lower()

    if use_regex:
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            if match_beginning:
                return bool(re.match(pattern, value, flags))
            return bool(re.search(pattern, value, flags))
        except re.error:
            return False

    if match_beginning:
        return value.startswith(pattern)
    return pattern in value
