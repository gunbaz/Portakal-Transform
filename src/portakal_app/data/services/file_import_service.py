from __future__ import annotations

import hashlib
import tempfile
from datetime import datetime
from pathlib import Path

import polars as pl

from portakal_app.data.errors import DatasetLoadError, UnsupportedFormatError
from portakal_app.data.models import DatasetHandle, SourceInfo, build_data_domain


class FileImportService:
    def load(self, path: str) -> DatasetHandle:
        source_path = Path(path).expanduser().resolve()
        if not source_path.exists() or not source_path.is_file():
            raise DatasetLoadError(f"Dataset file could not be found: {source_path}")

        file_format = self._detect_format(source_path)
        cache_path = self._cache_path_for(source_path)

        try:
            dataframe = self._read_dataframe(source_path, file_format)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            dataframe.write_parquet(cache_path)
        except UnsupportedFormatError:
            raise
        except Exception as exc:
            raise DatasetLoadError(f"Dataset could not be loaded from {source_path.name}.") from exc

        stat = source_path.stat()
        source = SourceInfo(
            path=source_path,
            format=file_format,
            size_bytes=int(stat.st_size),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            cache_path=cache_path,
        )
        domain = build_data_domain(dataframe)
        dataset_id = cache_path.stem
        return DatasetHandle(
            dataset_id=dataset_id,
            display_name=source_path.stem.replace("_", " ").title() or source_path.name,
            source=source,
            domain=domain,
            dataframe=dataframe,
            row_count=dataframe.height,
            column_count=dataframe.width,
            cache_path=cache_path,
        )

    def _read_dataframe(self, source_path: Path, file_format: str) -> pl.DataFrame:
        if file_format == "csv":
            return pl.read_csv(source_path)
        if file_format in {"tsv", "tab"}:
            return pl.read_csv(source_path, separator="\t")
        if file_format in {"xlsx", "xls"}:
            return pl.read_excel(source_path, engine="calamine")
        if file_format == "parquet":
            return pl.read_parquet(source_path)
        raise UnsupportedFormatError(f"Unsupported dataset format: {source_path.suffix.lower() or 'unknown'}")

    def _detect_format(self, source_path: Path) -> str:
        suffix = source_path.suffix.lower()
        mapping = {
            ".csv": "csv",
            ".tsv": "tsv",
            ".tab": "tab",
            ".xlsx": "xlsx",
            ".xls": "xls",
            ".parquet": "parquet",
        }
        file_format = mapping.get(suffix)
        if file_format is None:
            raise UnsupportedFormatError(f"Unsupported dataset format: {suffix or 'unknown'}")
        return file_format

    def _cache_path_for(self, source_path: Path) -> Path:
        stat = source_path.stat()
        fingerprint = hashlib.sha1(
            f"{source_path.resolve()}::{stat.st_mtime_ns}::{stat.st_size}".encode("utf-8")
        ).hexdigest()[:12]
        return Path(tempfile.gettempdir()) / "portakal-app" / "datasets" / f"{fingerprint}.parquet"
