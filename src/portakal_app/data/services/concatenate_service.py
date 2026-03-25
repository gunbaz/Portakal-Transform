from __future__ import annotations

from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


MERGE_MODES = ("Union", "Intersection")


class ConcatenateService:
    def concatenate(
        self,
        datasets: list[DatasetHandle],
        *,
        merge_mode: str = "Union",
        add_source_column: bool = False,
        source_column_name: str = "Source",
    ) -> DatasetHandle | None:
        if not datasets:
            return None

        dfs: list[pl.DataFrame] = []
        source_labels: list[str] = []

        for ds in datasets:
            dfs.append(ds.dataframe)
            source_labels.append(ds.display_name)

        if merge_mode == "Intersection":
            common_cols = set(dfs[0].columns)
            for df in dfs[1:]:
                common_cols &= set(df.columns)
            col_order = [c for c in dfs[0].columns if c in common_cols]
            dfs = [df.select(col_order) for df in dfs]
        else:
            all_cols: list[str] = []
            seen: set[str] = set()
            for df in dfs:
                for c in df.columns:
                    if c not in seen:
                        all_cols.append(c)
                        seen.add(c)
            aligned: list[pl.DataFrame] = []
            for df in dfs:
                missing = [c for c in all_cols if c not in df.columns]
                extra_df = df
                for mc in missing:
                    extra_df = extra_df.with_columns(pl.lit(None).alias(mc))
                aligned.append(extra_df.select(all_cols))
            dfs = aligned

        if add_source_column:
            tagged: list[pl.DataFrame] = []
            for df, label in zip(dfs, source_labels):
                tagged.append(df.with_columns(pl.lit(label).alias(source_column_name)))
            dfs = tagged

        result = pl.concat(dfs, how="vertical_relaxed")

        base = datasets[0]
        return replace(
            base,
            dataset_id=f"{base.dataset_id}-concatenated",
            display_name=f"{base.display_name} (concatenated)",
            dataframe=result,
            row_count=result.height,
            column_count=result.width,
            domain=build_data_domain(result),
        )
