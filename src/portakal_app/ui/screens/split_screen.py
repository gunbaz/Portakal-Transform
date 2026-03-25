from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.split_service import OUTPUT_TYPES, SplitService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class SplitScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = SplitService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        settings_group = QGroupBox("Split Settings")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setSpacing(8)

        col_row = QHBoxLayout()
        col_row.addWidget(QLabel("Column:"))
        self._column_combo = QComboBox()
        col_row.addWidget(self._column_combo, 1)
        settings_layout.addLayout(col_row)

        delim_row = QHBoxLayout()
        delim_row.addWidget(QLabel("Delimiter:"))
        self._delimiter_edit = QLineEdit(";")
        self._delimiter_edit.setMaximumWidth(60)
        delim_row.addWidget(self._delimiter_edit)
        delim_row.addStretch(1)
        settings_layout.addLayout(delim_row)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Output type:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(list(OUTPUT_TYPES))
        self._type_combo.setCurrentText("Numerical (0, 1)")
        type_row.addWidget(self._type_combo, 1)
        settings_layout.addLayout(type_row)

        layout.addWidget(settings_group)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        layout.addStretch(1)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self._apply_button = QPushButton("Apply")
        self._apply_button.setProperty("primary", True)
        self._apply_button.clicked.connect(self._apply)
        footer.addWidget(self._apply_button)
        layout.addLayout(footer)

    def set_input_payload(self, payload) -> None:
        dataset = payload.dataset if payload is not None else None
        self._dataset_handle = dataset
        self._output_dataset = None
        self._column_combo.clear()

        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
            for col in dataset.domain.columns:
                if col.logical_type in ("text", "categorical"):
                    self._column_combo.addItem(col.name)
        else:
            self._dataset_label.setText("Dataset: none")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "column": self._column_combo.currentText(),
            "delimiter": self._delimiter_edit.text(),
            "output_type": self._type_combo.currentText(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        col = str(payload.get("column", ""))
        if col and self._column_combo.findText(col) >= 0:
            self._column_combo.setCurrentText(col)
        self._delimiter_edit.setText(str(payload.get("delimiter", ";")))
        ot = str(payload.get("output_type", "Numerical (0, 1)"))
        if self._type_combo.findText(ot) >= 0:
            self._type_combo.setCurrentText(ot)

    def help_text(self) -> str:
        return "Split a string column by a delimiter and create indicator columns for each unique value."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/split/"

    def _apply(self) -> None:
        if self._dataset_handle is None or not self._column_combo.currentText():
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        self._output_dataset = self._service.split_column(
            self._dataset_handle,
            column_name=self._column_combo.currentText(),
            delimiter=self._delimiter_edit.text() or ";",
            output_type=self._type_combo.currentText(),
        )

        new_cols = self._output_dataset.column_count - self._dataset_handle.column_count
        self._result_label.setText(f"Added {new_cols} indicator column(s)")
        self._notify_output_changed()
