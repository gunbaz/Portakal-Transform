from __future__ import annotations

import io
import contextlib
import tempfile
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import polars as pl

from portakal_app.data.models import DatasetHandle, SourceInfo, build_data_domain


class PythonScriptResult:
    """Holds the result of a Python script execution."""

    def __init__(
        self,
        output_dataset: DatasetHandle | None = None,
        stdout: str = "",
        error: str = "",
    ) -> None:
        self.output_dataset = output_dataset
        self.stdout = stdout
        self.error = error


class PythonScriptService:
    def execute(
        self,
        dataset: DatasetHandle | None,
        *,
        code: str,
    ) -> PythonScriptResult:
        """Execute user-provided Python code with the input dataset.

        The code receives:
          - `in_data`: the input Polars DataFrame (or None)
          - `pl`: the polars module
        The code should assign the result to `out_data` (a pl.DataFrame).
        """
        if not code.strip():
            return PythonScriptResult(
                output_dataset=dataset,
                stdout="",
                error="No code provided.",
            )

        in_df = dataset.dataframe if dataset else None

        try:
            from PySide6 import QtCore, QtWidgets, QtGui
        except ImportError:
            QtCore = QtWidgets = QtGui = None

        namespace = {
            "in_data": in_df,
            "out_data": None,
            "pl": pl,
        }

        if QtCore is not None:
            # Expose standard Qt classes to the python script so legacy interactive scripts work
            namespace.update({
                "QEvent": QtCore.QEvent,
                "Qt": QtCore.Qt,
                "QtCore": QtCore,
                "QtWidgets": QtWidgets,
                "QtGui": QtGui,
            })

        stdout_capture = io.StringIO()
        error_msg = ""

        try:
            with contextlib.redirect_stdout(stdout_capture):
                exec(code, namespace)  # noqa: S102
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"

        stdout_text = stdout_capture.getvalue()
        out_df = namespace.get("out_data")

        if error_msg:
            return PythonScriptResult(
                output_dataset=None,
                stdout=stdout_text,
                error=error_msg,
            )

        if out_df is None:
            return PythonScriptResult(
                output_dataset=dataset,
                stdout=stdout_text,
                error="",
            )

        if not isinstance(out_df, pl.DataFrame):
            return PythonScriptResult(
                output_dataset=None,
                stdout=stdout_text,
                error=f"out_data must be a polars DataFrame, got {type(out_df).__name__}",
            )

        if dataset is not None:
            output = replace(
                dataset,
                dataset_id=f"{dataset.dataset_id}-script",
                display_name=f"{dataset.display_name} (script)",
                dataframe=out_df,
                row_count=out_df.height,
                column_count=out_df.width,
                domain=build_data_domain(out_df),
            )
        else:
            dummy_path = Path(tempfile.gettempdir()) / "portakal-app" / "script-output.parquet"
            output = DatasetHandle(
                dataset_id="script-output",
                display_name="Script Output",
                source=SourceInfo(
                    path=dummy_path,
                    format="script",
                    size_bytes=0,
                    modified_at=datetime.now(),
                    cache_path=dummy_path,
                ),
                dataframe=out_df,
                row_count=out_df.height,
                column_count=out_df.width,
                domain=build_data_domain(out_df),
                cache_path=dummy_path,
            )

        return PythonScriptResult(
            output_dataset=output,
            stdout=stdout_text,
            error="",
        )
