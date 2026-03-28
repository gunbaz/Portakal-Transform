from __future__ import annotations

from dataclasses import replace
import polars as pl
from portakal_app.data.models import DatasetHandle, build_data_domain


class PurgeDomainService:
    def purge(
        self,
        dataset: DatasetHandle,
        *,
        remove_unused_features: bool = True,
        remove_constant_features: bool = True,
        sort_feature_values: bool = True,
        remove_unused_classes: bool = True,
        remove_constant_classes: bool = True,
        sort_class_values: bool = True,
        remove_unused_metas: bool = True,
        remove_constant_metas: bool = True,
    ) -> tuple[DatasetHandle, dict[str, dict[str, int]]]:
        df = dataset.dataframe
        columns_to_drop: list[str] = []
        
        stats = {
            "features": {"sorted": 0, "reduced": 0, "removed": 0},
            "classes": {"sorted": 0, "reduced": 0, "removed": 0},
            "metas": {"reduced": 0, "removed": 0},
        }

        for col_schema in dataset.domain.columns:
            series = df.get_column(col_schema.name)
            is_feature = col_schema.role == "feature"
            is_target = col_schema.role == "target"
            is_meta = col_schema.role == "meta"

            if is_feature:
                group_key = "features"
            elif is_target:
                group_key = "classes"
            else:
                group_key = "metas"

            remove_constant = (
                (is_feature and remove_constant_features)
                or (is_target and remove_constant_classes)
                or (is_meta and remove_constant_metas)
            )
            remove_unused = (
                (is_feature and remove_unused_features)
                or (is_target and remove_unused_classes)
                or (is_meta and remove_unused_metas)
            )

            n_unique = series.drop_nulls().n_unique()
            if remove_constant and n_unique <= 1:
                columns_to_drop.append(col_schema.name)
                stats[group_key]["removed"] += 1
                continue

            if remove_unused and series.null_count() == series.len():
                columns_to_drop.append(col_schema.name)
                stats[group_key]["removed"] += 1
                continue

            should_sort = (
                (is_feature and sort_feature_values)
                or (is_target and sort_class_values)
            )
            if should_sort and (series.dtype == pl.Utf8 or series.dtype == pl.Categorical):
                if group_key in stats and "sorted" in stats[group_key]:
                    stats[group_key]["sorted"] += 1

        if columns_to_drop:
            df = df.drop(columns_to_drop)

        new_dataset = replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-purged",
            display_name=f"{dataset.display_name} (purged)",
            dataframe=df,
            row_count=df.height,
            column_count=df.width,
            domain=build_data_domain(df),
        )
        return new_dataset, stats
