from __future__ import annotations

import random
from dataclasses import replace

from portakal_app.data.models import DatasetHandle, build_data_domain


class DataSamplerService:
    """Data sampling service aligned with Orange Data Mining standards.

    Key behaviours that match Orange:
    * Shuffle before every sampling mode so row-order bias is eliminated.
    * Bootstrap remaining = true Out-of-Bag (indices never drawn).
    * Cross-validation: Data Sample = Train, Remaining Data = Test.
    * Output column order: Target → Meta → Features.
    """

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

        # ------------------------------------------------------------------
        # Fixed Proportion
        # ------------------------------------------------------------------
        if mode == "percentage":
            sample_size = max(1, int(n * percentage / 100))
            if stratify:
                sample_idx = _stratified_sample(rng, dataset, sample_size, with_replacement)
            else:
                sample_idx = _sample_indices(rng, n, sample_size, with_replacement)
            remaining_idx = sorted(set(range(n)) - set(sample_idx))
            if not with_replacement:
                sample_idx = sorted(set(sample_idx))

        # ------------------------------------------------------------------
        # Fixed Size
        # ------------------------------------------------------------------
        elif mode == "fixed":
            if not with_replacement:
                sample_size = min(fixed_size, n)
            else:
                sample_size = fixed_size
            if stratify:
                sample_idx = _stratified_sample(rng, dataset, sample_size, with_replacement)
            else:
                sample_idx = _sample_indices(rng, n, sample_size, with_replacement)
            remaining_idx = sorted(set(range(n)) - set(sample_idx))
            if not with_replacement:
                sample_idx = sorted(set(sample_idx))

        # ------------------------------------------------------------------
        # Cross Validation  (Orange standard port mapping)
        #   Data Sample  → Train  (all folds except the held-out one)
        #   Remaining    → Test   (the held-out fold)
        # ------------------------------------------------------------------
        elif mode == "cross-validation":
            # Shuffle before splitting – matches Orange's KFold(shuffle=True)
            shuffled = list(range(n))
            rng.shuffle(shuffled)

            fold_size = n // folds
            fold_buckets: list[list[int]] = []
            for f in range(folds):
                start = f * fold_size
                end = (start + fold_size) if f < folds - 1 else n
                fold_buckets.append(shuffled[start:end])

            test_idx = sorted(fold_buckets[selected_fold - 1])
            train_idx = sorted(
                idx
                for f, bucket in enumerate(fold_buckets)
                if f != selected_fold - 1
                for idx in bucket
            )

            train_df = _reorder_columns(df[train_idx], dataset.domain)
            test_df = _reorder_columns(df[test_idx], dataset.domain)
            return _build_pair(dataset, train_df, test_df)

        # ------------------------------------------------------------------
        # Bootstrap  (Out-of-Bag = indices never drawn)
        # ------------------------------------------------------------------
        elif mode == "bootstrap":
            # Draw N indices with replacement (sample size fixed to N)
            bootstrap_idx = [rng.randint(0, n - 1) for _ in range(n)]
            bootstrap_idx.sort()

            # True OOB via boolean mask (matches Orange's SampleBootstrap)
            selected = [False] * n
            for i in bootstrap_idx:
                selected[i] = True
            oob_idx = [i for i in range(n) if not selected[i]]

            sample_df = _reorder_columns(df[bootstrap_idx], dataset.domain)
            oob_df = _reorder_columns(df[oob_idx], dataset.domain) if oob_idx else None
            return _build_pair(dataset, sample_df, oob_df)

        else:
            sample_idx = list(range(n))
            remaining_idx = []

        sample_df = _reorder_columns(df[sample_idx], dataset.domain)
        remaining_df = (
            _reorder_columns(df[remaining_idx], dataset.domain)
            if remaining_idx
            else None
        )
        return _build_pair(dataset, sample_df, remaining_df)


# ── helpers ───────────────────────────────────────────────────────────────


def _reorder_columns(df, domain) -> object:
    """Reorder columns: Target → Meta → Features (global hierarchy)."""
    if domain is None:
        return df
    target_names = [c.name for c in domain.target_columns if c.name in df.columns]
    meta_names = [c.name for c in domain.meta_columns if c.name in df.columns]
    feature_names = [c.name for c in domain.feature_columns if c.name in df.columns]
    ordered = target_names + meta_names + feature_names
    seen = set(ordered)
    extras = [c for c in df.columns if c not in seen]
    final_order = ordered + extras
    if final_order == list(df.columns):
        return df
    return df.select(final_order)


def _sample_indices(
    rng: random.Random, n: int, size: int, with_replacement: bool
) -> list[int]:
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
            indices.extend(
                rng.sample(group_indices, min(group_size, len(group_indices)))
            )
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
