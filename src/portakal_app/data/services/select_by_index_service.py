from __future__ import annotations

from dataclasses import replace

from portakal_app.data.models import DatasetHandle, build_data_domain


class SelectByIndexService:
    def select(
        self,
        data: DatasetHandle,
        subset: DatasetHandle,
    ) -> tuple[DatasetHandle | None, DatasetHandle | None]:
        data_ids = set(range(data.row_count))
        subset_size = min(subset.row_count, data.row_count)
        matching_indices = set(range(subset_size))
        non_matching_indices = data_ids - matching_indices

        if not matching_indices:
            return None, data

        matching_df = data.dataframe[sorted(matching_indices)]
        non_matching_df = data.dataframe[sorted(non_matching_indices)] if non_matching_indices else None

        matching = replace(
            data,
            dataset_id=f"{data.dataset_id}-matching",
            display_name=f"{data.display_name} (matching)",
            dataframe=matching_df,
            row_count=matching_df.height,
            domain=build_data_domain(matching_df),
        )

        non_matching = None
        if non_matching_df is not None and non_matching_df.height > 0:
            non_matching = replace(
                data,
                dataset_id=f"{data.dataset_id}-non-matching",
                display_name=f"{data.display_name} (non-matching)",
                dataframe=non_matching_df,
                row_count=non_matching_df.height,
                domain=build_data_domain(non_matching_df),
            )

        return matching, non_matching
