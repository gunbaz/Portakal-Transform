from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.python_script_service import PythonScriptService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport

_DEFAULT_CODE = """\
# Available variables:
#   in_data  - input Polars DataFrame (or None)
#   pl       - the polars module
#
# Assign result to out_data:
#   out_data = in_data.filter(pl.col("x") > 0)

out_data = in_data
"""


class PythonScriptScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = PythonScriptService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self._code_edit = QPlainTextEdit()
        self._code_edit.setPlainText(_DEFAULT_CODE)
        self._code_edit.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 10pt;"
        )
        self._code_edit.setTabStopDistance(32.0)
        splitter.addWidget(self._code_edit)

        self._output_text = QPlainTextEdit()
        self._output_text.setReadOnly(True)
        self._output_text.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 9pt; "
            "background: #1e1e1e; color: #d4d4d4;"
        )
        self._output_text.setMaximumHeight(150)
        splitter.addWidget(self._output_text)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self._run_button = QPushButton("Run")
        self._run_button.setProperty("primary", True)
        self._run_button.clicked.connect(self._apply)
        footer.addWidget(self._run_button)
        layout.addLayout(footer)

    def set_input_payload(self, payload) -> None:
        dataset = payload.dataset if payload is not None else None
        self._dataset_handle = dataset
        self._output_dataset = None

        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
        else:
            self._dataset_label.setText("Dataset: none")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {"code": self._code_edit.toPlainText()}

    def restore_node_state(self, payload: dict[str, object]) -> None:
        code = payload.get("code", "")
        if code:
            self._code_edit.setPlainText(str(code))

    def help_text(self) -> str:
        return "Write and execute custom Python/Polars code to transform the input data."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/pythonscript/"

    def _apply(self) -> None:
        code = self._code_edit.toPlainText()
        result = self._service.execute(self._dataset_handle, code=code)

        output_lines = []
        if result.stdout:
            output_lines.append(result.stdout)
        if result.error:
            output_lines.append(f"ERROR: {result.error}")

        self._output_text.setPlainText("\n".join(output_lines) if output_lines else "(no output)")

        self._output_dataset = result.output_dataset

        if result.error:
            self._result_label.setText(f"Error: {result.error}")
        elif self._output_dataset:
            self._result_label.setText(
                f"Output: {self._output_dataset.row_count}r x {self._output_dataset.column_count}c"
            )
        else:
            self._result_label.setText("No output data.")

        self._notify_output_changed()
