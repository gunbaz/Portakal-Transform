from __future__ import annotations

from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


AGGREGATIONS = (
    "Mean", "Median", "Min", "Max", "Sum", "Count",
    "First", "Last", "Std", "Variance", "Mode",
)


class GroupByService:
    def group_by(
        self,
        dataset: DatasetHandle,
        *,
        group_columns: list[str],
        aggregations: dict[str, list[str]],
    ) -> DatasetHandle:
        df = dataset.dataframe

        if not group_columns:
            return dataset

        valid_group_cols = [c for c in group_columns if c in df.columns]
        if not valid_group_cols:
            return dataset

        agg_exprs: list[pl.Expr] = []
        for col_name, agg_list in aggregations.items():
            if col_name not in df.columns or col_name in valid_group_cols:
                continue
            for agg in agg_list:
                expr = _build_agg_expr(col_name, agg)
                if expr is not None:
                    agg_exprs.append(expr)

        if not agg_exprs:
            agg_exprs = [pl.len().alias("count")]

        result = df.group_by(valid_group_cols, maintain_order=True).agg(agg_exprs)

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-grouped",
            display_name=f"{dataset.display_name} (grouped)",
            dataframe=result,
            row_count=result.height,
            column_count=result.width,
            domain=build_data_domain(result),
        )


def _build_agg_expr(col_name: str, agg: str) -> pl.Expr | None:
    alias = f"{col_name}_{agg.lower()}"
    col = pl.col(col_name)
    if agg == "Mean":
        return col.mean().alias(alias)
    if agg == "Median":
        return col.median().alias(alias)
    if agg == "Min":
        return col.min().alias(alias)
    if agg == "Max":
        return col.max().alias(alias)
    if agg == "Sum":
        return col.sum().alias(alias)
    if agg == "Count":
        return col.count().alias(alias)
    if agg == "First":
        return col.first().alias(alias)
    if agg == "Last":
        return col.last().alias(alias)
    if agg == "Std":
        return col.std().alias(alias)
    if agg == "Variance":
        return col.var().alias(alias)
    if agg == "Mode":
        return col.mode().first().alias(alias)
    return None
