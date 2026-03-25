from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.aggregate_columns_service import OPERATIONS, AggregateColumnsService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class AggregateColumnsScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = AggregateColumnsService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        cols_group = QGroupBox("Select Columns")
        cols_layout = QVBoxLayout(cols_group)
        cols_layout.setContentsMargins(10, 10, 10, 10)
        cols_layout.setSpacing(8)

        self._column_list = QListWidget()
        self._column_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        cols_layout.addWidget(self._column_list)
        layout.addWidget(cols_group, 1)

        settings_group = QGroupBox("Aggregation")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setSpacing(8)

        op_row = QHBoxLayout()
        op_row.addWidget(QLabel("Operation:"))
        self._op_combo = QComboBox()
        self._op_combo.addItems(list(OPERATIONS.keys()))
        self._op_combo.setCurrentText("Mean")
        op_row.addWidget(self._op_combo, 1)
        settings_layout.addLayout(op_row)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Output column:"))
        self._output_name = QLineEdit("agg")
        name_row.addWidget(self._output_name, 1)
        settings_layout.addLayout(name_row)

        layout.addWidget(settings_group)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

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
        self._column_list.clear()

        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
            for col in dataset.domain.columns:
                if col.logical_type == "numeric":
                    item = QListWidgetItem(col.name)
                    item.setSelected(True)
                    self._column_list.addItem(item)
        else:
            self._dataset_label.setText("Dataset: none")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        selected = [
            self._column_list.item(i).text()
            for i in range(self._column_list.count())
            if self._column_list.item(i).isSelected()
        ]
        return {
            "columns": selected,
            "operation": self._op_combo.currentText(),
            "output_name": self._output_name.text(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        cols = payload.get("columns", [])
        if isinstance(cols, list):
            for i in range(self._column_list.count()):
                item = self._column_list.item(i)
                item.setSelected(item.text() in cols)
        op = str(payload.get("operation", "Mean"))
        if self._op_combo.findText(op) >= 0:
            self._op_combo.setCurrentText(op)
        self._output_name.setText(str(payload.get("output_name", "agg")))

    def help_text(self) -> str:
        return "Compute a row-wise aggregation (sum, mean, etc.) over selected numeric columns."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/aggregate-columns/"

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        selected = [
            self._column_list.item(i).text()
            for i in range(self._column_list.count())
            if self._column_list.item(i).isSelected()
        ]

        self._output_dataset = self._service.aggregate(
            self._dataset_handle,
            columns=selected,
            operation=self._op_combo.currentText(),
            output_name=self._output_name.text() or "agg",
        )

        self._result_label.setText(
            f"{self._op_combo.currentText()} of {len(selected)} column(s) -> '{self._output_name.text()}'"
        )
        self._notify_output_changed()
