from __future__ import annotations

from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


DEFAULT_ROW_NAME = "row"


class MeltService:
    def melt(
        self,
        dataset: DatasetHandle,
        *,
        id_column: str | None = None,
        ignore_non_numeric: bool = True,
        exclude_zeros: bool = False,
        item_name: str = "item",
        value_name: str = "value",
    ) -> DatasetHandle | None:
        """Reshape wide data to long format, matching Orange3 OWMelt logic."""
        df = dataset.dataframe

        # --- determine which feature columns will be melted ----------------
        feature_names = {c.name for c in dataset.domain.feature_columns}

        # Build useful_vars: feature columns that are candidates for melting
        if ignore_non_numeric:
            numeric_logical = {
                col.name
                for col in dataset.domain.feature_columns
                if col.logical_type in ("numeric", "boolean")
            }
            useful_vars = [
                c for c in df.columns
                if c in feature_names and c in numeric_logical
            ]
        else:
            useful_vars = [c for c in df.columns if c in feature_names]

        # The id column must not be melted
        if id_column and id_column in df.columns:
            useful_vars = [c for c in useful_vars if c != id_column]

        if not useful_vars:
            return None  # nothing to melt → caller should show error

        # --- build id column -----------------------------------------------
        id_vars: list[str] = []
        work_df = df

        if id_column and id_column in df.columns:
            id_vars = [id_column]
            # Remove rows where id is null/empty (Orange3 does the same)
            id_dtype = work_df.schema[id_column]
            if id_dtype == pl.Utf8 or id_dtype == pl.Categorical:
                work_df = work_df.filter(
                    pl.col(id_column).is_not_null()
                    & (pl.col(id_column).cast(pl.Utf8) != "")
                )
            else:
                work_df = work_df.filter(pl.col(id_column).is_not_null())
        else:
            # No id column selected → add a row-number column (Orange3 adds
            # ContinuousVariable("row") with 0-based indices)
            row_col_name = item_name  # avoid clash
            row_col_name = DEFAULT_ROW_NAME
            # Ensure unique name
            while row_col_name in work_df.columns or row_col_name in (item_name, value_name):
                row_col_name = row_col_name + "_"
            work_df = work_df.with_row_index(name=row_col_name)
            id_vars = [row_col_name]

        # --- unpivot -------------------------------------------------------
        melted = work_df.unpivot(
            on=useful_vars,
            index=id_vars,
            variable_name=item_name,
            value_name=value_name,
        )

        # --- filter NaN / null values (Orange3 always does this) -----------
        val_col = pl.col(value_name)
        try:
            melted = melted.with_columns(val_col.cast(pl.Float64, strict=False))
        except Exception:
            pass

        # Remove null / NaN rows
        melted = melted.filter(val_col.is_not_null() & val_col.is_not_nan())

        # --- exclude zeros -------------------------------------------------
        if exclude_zeros:
            if not ignore_non_numeric:
                # When non-numeric (discrete) features are included,
                # Orange3 keeps discrete rows even when their value == 0.
                discrete_names = {
                    col.name
                    for col in dataset.domain.feature_columns
                    if col.logical_type not in ("numeric", "boolean")
                }
                is_discrete_row = pl.col(item_name).is_in(list(discrete_names))
                melted = melted.filter(is_discrete_row | (val_col != 0.0))
            else:
                melted = melted.filter(val_col != 0.0)

        # --- build output --------------------------------------------------
        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-melted",
            display_name=f"{dataset.display_name} (melted)",
            dataframe=melted,
            row_count=melted.height,
            column_count=melted.width,
            domain=build_data_domain(melted, source_domain=dataset.domain),
        )
