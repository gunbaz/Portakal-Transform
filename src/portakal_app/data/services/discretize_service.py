from __future__ import annotations

from dataclasses import replace

import polars as pl

from portakal_app.data.models import DatasetHandle, build_data_domain


METHODS = (
    "Equal Width",
    "Equal Frequency",
    "Remove",
    "Keep Numeric",
)


class DiscretizeService:
    def discretize(
        self,
        dataset: DatasetHandle,
        *,
        method: str = "Equal Width",
        n_bins: int = 4,
    ) -> DatasetHandle:
        df = dataset.dataframe
        new_columns: dict[str, pl.Series] = {}

        for col_name in df.columns:
            series = df.get_column(col_name)
            if not series.dtype.is_numeric():
                new_columns[col_name] = series
                continue

            if method == "Keep Numeric":
                new_columns[col_name] = series
            elif method == "Remove":
                continue
            elif method == "Equal Width":
                new_columns[col_name] = _equal_width_bin(series, col_name, n_bins)
            elif method == "Equal Frequency":
                new_columns[col_name] = _equal_freq_bin(series, col_name, n_bins)
            else:
                new_columns[col_name] = series

        result_df = pl.DataFrame(new_columns)

        return replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-discretized",
            display_name=f"{dataset.display_name} (discretized)",
            dataframe=result_df,
            row_count=result_df.height,
            column_count=result_df.width,
            domain=build_data_domain(result_df),
        )


def _equal_width_bin(series: pl.Series, name: str, n_bins: int) -> pl.Series:
    non_null = series.drop_nulls()
    if non_null.len() == 0:
        return pl.Series(name, ["?"] * series.len(), dtype=pl.Utf8)

    min_val = float(non_null.min())
    max_val = float(non_null.max())

    if min_val == max_val:
        return pl.Series(name, [f"[{min_val:.2f}]"] * series.len(), dtype=pl.Utf8)

    step = (max_val - min_val) / n_bins
    labels: list[str | None] = []
    for val in series.to_list():
        if val is None:
            labels.append(None)
        else:
            fval = float(val)
            bin_idx = min(int((fval - min_val) / step), n_bins - 1)
            lo = min_val + bin_idx * step
            hi = lo + step
            labels.append(f"[{lo:.2f}, {hi:.2f})")
    return pl.Series(name, labels, dtype=pl.Utf8)


def _equal_freq_bin(series: pl.Series, name: str, n_bins: int) -> pl.Series:
    non_null = series.drop_nulls()
    if non_null.len() == 0:
        return pl.Series(name, ["?"] * series.len(), dtype=pl.Utf8)

    sorted_vals = sorted(non_null.to_list())
    bin_size = max(1, len(sorted_vals) // n_bins)
    thresholds: list[float] = []
    for i in range(1, n_bins):
        idx = min(i * bin_size, len(sorted_vals) - 1)
        thresholds.append(float(sorted_vals[idx]))

    labels: list[str | None] = []
    for val in series.to_list():
        if val is None:
            labels.append(None)
        else:
            fval = float(val)
            bin_idx = 0
            for t in thresholds:
                if fval >= t:
                    bin_idx += 1
            if bin_idx == 0:
                labels.append(f"< {thresholds[0]:.2f}")
            elif bin_idx >= len(thresholds):
                labels.append(f">= {thresholds[-1]:.2f}")
            else:
                labels.append(f"[{thresholds[bin_idx - 1]:.2f}, {thresholds[bin_idx]:.2f})")
    return pl.Series(name, labels, dtype=pl.Utf8)
