from __future__ import annotations

import math
from dataclasses import replace
import polars as pl
from portakal_app.data.models import DatasetHandle, build_data_domain

METHODS = (
    "Keep numeric",
    "Remove",
    "Natural binning",
    "Fixed width",
    "Time interval",
    "Equal frequency",
    "Equal width",
    "Entropy vs. MDL",
    "Custom",
    "Use default setting"
)

class DiscretizeService:
    def discretize(
        self,
        dataset: DatasetHandle,
        *,
        default_method: str = "Keep numeric",
        default_n_bins: int = 4,
        column_methods: dict[str, dict[str, object]] | None = None,
    ) -> DatasetHandle:
        df = dataset.dataframe
        new_columns: dict[str, pl.Series] = {}
        col_methods = column_methods or {}

        for col_name in df.columns:
            series = df.get_column(col_name)
            
            # Non-numeric columns are just passed through
            if not series.dtype.is_numeric():
                new_columns[col_name] = series
                continue

            method_params = col_methods.get(col_name, {})
            method = method_params.get("method", "Use default setting")
            
            if method == "Use default setting":
                method = default_method
                params = {"n_bins": default_n_bins}
            else:
                params = method_params

            if method == "Keep numeric":
                new_columns[col_name] = series
            elif method == "Remove":
                continue
            elif method in ("Equal width", "Natural binning"):
                n_bins = int(params.get("n_bins", default_n_bins))
                new_columns[col_name] = _equal_width_bin(series, col_name, max(2, n_bins))
            elif method == "Equal frequency":
                n_bins = int(params.get("n_bins", default_n_bins))
                new_columns[col_name] = _equal_freq_bin(series, col_name, max(2, n_bins))
            elif method == "Fixed width":
                width = float(params.get("width", 1.0))
                new_columns[col_name] = _fixed_width_bin(series, col_name, width)
            elif method == "Custom":
                cuts_str = str(params.get("cuts", ""))
                try:
                    cuts = [float(x.strip()) for x in cuts_str.split(",") if x.strip()]
                    new_columns[col_name] = _custom_bin(series, col_name, cuts)
                except ValueError:
                    # fallback to keep if badly formatted
                    new_columns[col_name] = series
            else:
                # Stub for "Entropy vs. MDL" or "Time interval"
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
    
    # Needs to be dict encoded for Polars categorical/ordinal if we want proper sort,
    # but for Portakal logic, string representation is temporarily fine to mimic Orange's physical discretization.
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

    if not thresholds:
        return pl.Series(name, [f"[{sorted_vals[0]:.2f}]"] * series.len(), dtype=pl.Utf8)

    return _custom_bin(series, name, thresholds)

def _fixed_width_bin(series: pl.Series, name: str, width: float) -> pl.Series:
    if width <= 0:
        return series
    
    labels: list[str | None] = []
    for val in series.to_list():
        if val is None:
            labels.append(None)
        else:
            fval = float(val)
            base = math.floor(fval / width) * width
            labels.append(f"[{base:.2f}, {base + width:.2f})")
    return pl.Series(name, labels, dtype=pl.Utf8)

def _custom_bin(series: pl.Series, name: str, thresholds: list[float]) -> pl.Series:
    thresholds = sorted(list(set(thresholds)))
    if not thresholds:
        return series
        
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
