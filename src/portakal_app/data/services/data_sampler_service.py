from __future__ import annotations

import random
from dataclasses import replace

from portakal_app.data.models import DatasetHandle, build_data_domain


class DataSamplerService:
    def sample(
        self,
        dataset: DatasetHandle,
        *,
        mode: str = "percentage",
        percentage: int = 70,
        fixed_size: int = 10,
        folds: int = 10,
        selected_fold: int = 1,
        with_replacement: bool = False,
        stratify: bool = False,
        seed: int | None = None,
    ) -> tuple[DatasetHandle, DatasetHandle | None]:
        df = dataset.dataframe
        n = df.height
        rng = random.Random(seed)

        if mode == "percentage":
            sample_size = max(1, int(n * percentage / 100))
            if stratify:
                indices = _stratified_sample(rng, dataset, sample_size, with_replacement)
            else:
                indices = _sample_indices(rng, n, sample_size, with_replacement)
        elif mode == "fixed":
            sample_size = min(fixed_size, n)
            if stratify:
                indices = _stratified_sample(rng, dataset, sample_size, with_replacement)
            else:
                indices = _sample_indices(rng, n, sample_size, with_replacement)
        elif mode == "cross-validation":
            fold_size = n // folds
            start = (selected_fold - 1) * fold_size
            end = start + fold_size if selected_fold < folds else n
            all_indices = set(range(n))
            fold_indices = set(range(start, end))
            remaining = sorted(all_indices - fold_indices)
            indices = sorted(fold_indices)
            sample_df = df[indices]
            remaining_df = df[remaining]
            return _build_pair(dataset, sample_df, remaining_df)
        elif mode == "bootstrap":
            indices = [rng.randint(0, n - 1) for _ in range(n)]
            unique_indices = set(indices)
            remaining_indices = sorted(set(range(n)) - unique_indices)
            sample_df = df[indices]
            remaining_df = df[remaining_indices] if remaining_indices else None
            sample_ds = replace(
                dataset,
                dataset_id=f"{dataset.dataset_id}-sample",
                display_name=f"{dataset.display_name} (sample)",
                dataframe=sample_df,
                row_count=sample_df.height,
                domain=build_data_domain(sample_df),
            )
            remaining_ds = None
            if remaining_df is not None and remaining_df.height > 0:
                remaining_ds = replace(
                    dataset,
                    dataset_id=f"{dataset.dataset_id}-remaining",
                    display_name=f"{dataset.display_name} (remaining)",
                    dataframe=remaining_df,
                    row_count=remaining_df.height,
                    domain=build_data_domain(remaining_df),
                )
            return sample_ds, remaining_ds
        else:
            indices = list(range(n))

        sample_indices = sorted(set(indices)) if not with_replacement else indices
        remaining_indices = sorted(set(range(n)) - set(indices))

        sample_df = df[sample_indices]
        remaining_df = df[remaining_indices] if remaining_indices else None
        return _build_pair(dataset, sample_df, remaining_df)


def _sample_indices(rng: random.Random, n: int, size: int, with_replacement: bool) -> list[int]:
    if with_replacement:
        return [rng.randint(0, n - 1) for _ in range(size)]
    return rng.sample(range(n), min(size, n))


def _stratified_sample(
    rng: random.Random,
    dataset: DatasetHandle,
    sample_size: int,
    with_replacement: bool,
) -> list[int]:
    target_cols = dataset.domain.target_columns if dataset.domain else ()
    if not target_cols:
        return _sample_indices(rng, dataset.dataframe.height, sample_size, with_replacement)

    target_name = target_cols[0].name
    series = dataset.dataframe.get_column(target_name)
    groups: dict[str, list[int]] = {}
    for i, val in enumerate(series.to_list()):
        key = str(val)
        groups.setdefault(key, []).append(i)

    n = dataset.dataframe.height
    indices: list[int] = []
    for group_indices in groups.values():
        group_size = max(1, round(len(group_indices) / n * sample_size))
        if with_replacement:
            indices.extend(rng.choices(group_indices, k=group_size))
        else:
            indices.extend(rng.sample(group_indices, min(group_size, len(group_indices))))
    return indices


def _build_pair(
    dataset: DatasetHandle,
    sample_df,
    remaining_df,
) -> tuple[DatasetHandle, DatasetHandle | None]:
    sample_ds = replace(
        dataset,
        dataset_id=f"{dataset.dataset_id}-sample",
        display_name=f"{dataset.display_name} (sample)",
        dataframe=sample_df,
        row_count=sample_df.height,
        domain=build_data_domain(sample_df),
    )
    remaining_ds = None
    if remaining_df is not None and remaining_df.height > 0:
        remaining_ds = replace(
            dataset,
            dataset_id=f"{dataset.dataset_id}-remaining",
            display_name=f"{dataset.display_name} (remaining)",
            dataframe=remaining_df,
            row_count=remaining_df.height,
            domain=build_data_domain(remaining_df),
        )
    return sample_ds, remaining_ds
