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
            from PySide6.QtCore import Qt, QEvent, QObject, QTimer, Signal, Slot
        except ImportError:
            QtCore = QtWidgets = QtGui = Qt = QEvent = QObject = QTimer = Signal = Slot = None

        namespace = {
            "in_data": in_df,
            "out_data": None,
            "pl": pl,
            "Qt": Qt,
            "QEvent": QEvent,
            "QObject": QObject,
            "QTimer": QTimer,
            "Signal": Signal,
            "Slot": Slot,
            "QtCore": QtCore,
            "QtWidgets": QtWidgets,
            "QtGui": QtGui,
        }

        # Add common libraries if available
        try:
            import numpy as np
            namespace["np"] = np
        except ImportError:
            pass
        try:
            import pandas as pd
            namespace["pd"] = pd
        except ImportError:
            pass
        try:
            import Orange
            namespace["Orange"] = Orange
            # If orange is available and in_data exists, provide it as an Orange Table too
            if in_df is not None:
                try:
                    # Conversion from polars to orange
                    import pandas as pd # Ensure pd is available for conversion
                    pdf = in_df.to_pandas()
                    # We might need to handle domain better, but for now:
                    namespace["orange_in_data"] = Orange.data.Table.from_pandas_dfs(pdf)
                    # If the script seems to prefer orange, swap in_data (OR provide it as a property)
                    if "in_data.X" in code or "in_data.domain" in code:
                        namespace["in_data"] = namespace["orange_in_data"]
                except Exception:
                    pass
        except ImportError:
            pass

        if QtCore is not None:
            # Expose standard Qt classes to the python script so legacy interactive scripts work
            for module in (QtCore, QtWidgets, QtGui):
                if module is None: continue
                for name in dir(module):
                    if not name.startswith("_") and name not in namespace:
                        try:
                            namespace[name] = getattr(module, name)
                        except AttributeError:
                            pass

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

        if out_df is not None:
            # Check for Orange Table output and convert to Polars
            try:
                import Orange
                if isinstance(out_df, Orange.data.Table):
                    import pandas as pd
                    # Convert Orange Table to Pandas then to Polars
                    # Simple conversion for now
                    # Attributes
                    pdf_x = pd.DataFrame(out_df.X, columns=[a.name for a in out_df.domain.attributes])
                    # Metas
                    pdf_m = pd.DataFrame(out_df.metas, columns=[m.name for m in out_df.domain.metas])
                    # Class
                    pdf_y = pd.Series(out_df.Y, name=out_df.domain.class_var.name if out_df.domain.class_var else "Y")
                    
                    combined = pd.concat([pdf_x, pdf_m, pdf_y], axis=1)
                    out_df = pl.from_pandas(combined)
            except Exception:
                pass

        if not isinstance(out_df, (pl.DataFrame, type(None))):
             # Fallback: if it has to_pandas (like pandas.DataFrame)
             if hasattr(out_df, "to_pandas"):
                 try:
                     out_df = pl.from_pandas(out_df.to_pandas())
                 except Exception:
                     pass

        if out_df is not None and not isinstance(out_df, pl.DataFrame):
            return PythonScriptResult(
                output_dataset=None,
                stdout=stdout_text,
                error=f"out_data must be a polars or orange DataFrame, got {type(out_df).__name__}",
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
