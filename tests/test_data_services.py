from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from portakal_app.data.errors import DatasetLoadError, UnsupportedFormatError
from portakal_app.data.services.file_import_service import FileImportService
from portakal_app.data.services.save_data_service import SaveDataService


@pytest.fixture()
def sample_dataframe() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "amount": [10.5, 20.0, 13.25],
            "event_time": ["2026-03-18 10:00", "2026-03-19 11:30", "2026-03-20 09:15"],
            "species": ["setosa", "versicolor", "setosa"],
        }
    )


def test_file_import_service_loads_csv_tsv_tab_xlsx_and_parquet(tmp_path, sample_dataframe):
    service = FileImportService()
    csv_path = tmp_path / "sample.csv"
    tsv_path = tmp_path / "sample.tsv"
    tab_path = tmp_path / "sample.tab"
    xlsx_path = tmp_path / "sample.xlsx"
    parquet_path = tmp_path / "sample.parquet"

    sample_dataframe.write_csv(csv_path)
    sample_dataframe.write_csv(tsv_path, separator="\t")
    sample_dataframe.write_csv(tab_path, separator="\t")
    sample_dataframe.write_excel(xlsx_path)
    sample_dataframe.write_parquet(parquet_path)

    for path in (csv_path, tsv_path, tab_path, xlsx_path, parquet_path):
        dataset = service.load(str(path))
        assert dataset.row_count == 3
        assert dataset.column_count == 3
        assert dataset.cache_path.exists()
        assert dataset.source.path == path


def test_file_import_service_raises_typed_error_for_missing_path(tmp_path):
    service = FileImportService()
    missing_path = tmp_path / "missing.csv"

    with pytest.raises(DatasetLoadError):
        service.load(str(missing_path))


def test_file_import_service_raises_typed_error_for_unsupported_format(tmp_path):
    service = FileImportService()
    unsupported_path = tmp_path / "sample.json"
    unsupported_path.write_text('{"a": 1}', encoding="utf-8")

    with pytest.raises(UnsupportedFormatError):
        service.load(str(unsupported_path))


def test_file_import_service_builds_expected_domain(sample_dataframe, tmp_path):
    service = FileImportService()
    csv_path = tmp_path / "domain.csv"
    sample_dataframe.write_csv(csv_path)

    dataset = service.load(str(csv_path))
    columns = {column.name: column for column in dataset.domain.columns}

    assert columns["amount"].logical_type == "numeric"
    assert columns["amount"].role == "feature"
    assert columns["event_time"].logical_type == "datetime"
    assert columns["species"].logical_type == "categorical"
    assert columns["species"].role == "target"


def test_save_data_service_exports_csv_xlsx_and_parquet_round_trip(tmp_path, sample_dataframe):
    import_service = FileImportService()
    save_service = SaveDataService()
    source_path = tmp_path / "source.csv"
    sample_dataframe.write_csv(source_path)
    dataset = import_service.load(str(source_path))

    for extension in ("csv", "xlsx", "parquet"):
        target_path = tmp_path / f"export.{extension}"
        save_service.save(dataset, str(target_path))
        reloaded = import_service.load(str(target_path))
        assert reloaded.row_count == dataset.row_count
        assert reloaded.column_count == dataset.column_count


def test_save_data_service_raises_typed_error_for_unsupported_export(tmp_path, sample_dataframe):
    import_service = FileImportService()
    save_service = SaveDataService()
    source_path = tmp_path / "source.csv"
    sample_dataframe.write_csv(source_path)
    dataset = import_service.load(str(source_path))

    with pytest.raises(UnsupportedFormatError):
        save_service.save(dataset, str(tmp_path / "export.tsv"))
