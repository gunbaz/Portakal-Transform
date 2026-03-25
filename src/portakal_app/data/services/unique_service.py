from __future__ import annotations

from dataclasses import replace

from portakal_app.data.models import DatasetHandle, build_data_domain


TIEBREAKERS = ("Last instance", "First instance", "Middle instance", "Random instance", "Discard non-unique")


class UniqueService:
    def filter_unique(
        self,
        dataset: DatasetHandle,
        *,
        group_by_columns: list[str],
        tiebreaker: str = "First instance",
    ) -> DatasetHandle:
        df = dataset.dataframe

        if not group_by_columns:
            return dataset

        if tiebreaker == "First instance":
            result = df.unique(subset=group_by_columns, keep="first", maintain_order=True)
        elif tiebreaker == "Last instance":
            result = df.unique(subset=group_by_columns, keep="last", maintain_order=True)
        elif tiebreaker == "Discard non-unique":
            result = df.unique(subset=group_by_columns, keep="none")
        elif tiebreaker == "Middle instance":
            groups = df.with_row_index("__row_idx__").group_by(group_by_columns, maintain_order=True)
            middle_indices: list[int] = []
            for _key, group_df in groups:
                indices = group_df.get_column("__row_idx__").to_list()
                middle_indices.append(indices[len(indices) // 2])
            result = df[middle_indices]
        elif tiebreaker == "Random instance":
            result = df.unique(subset=group_by_columns, keep="any", maintain_order=True)
        else:
            result = df.unique(subset=group_by_columns, keep="first", maintain_order=True)

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-unique",
            display_name=f"{dataset.display_name} (unique)",
            dataframe=result,
            row_count=result.height,
            domain=build_data_domain(result),
        )
