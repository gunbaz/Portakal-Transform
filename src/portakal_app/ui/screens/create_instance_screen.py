from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.create_instance_service import CreateInstanceService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class CreateInstanceScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = CreateInstanceService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None
        self._value_edits: dict[str, QLineEdit] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._fields_container = QWidget()
        self._fields_layout = QVBoxLayout(self._fields_container)
        self._fields_layout.setContentsMargins(0, 0, 0, 0)
        self._fields_layout.setSpacing(6)
        scroll.setWidget(self._fields_container)
        layout.addWidget(scroll, 1)

        opts_group = QGroupBox("Options")
        opts_layout = QVBoxLayout(opts_group)
        opts_layout.setContentsMargins(10, 10, 10, 10)
        self._append_cb = QCheckBox("Append to input data")
        opts_layout.addWidget(self._append_cb)

        defaults_row = QHBoxLayout()
        self._fill_median = QPushButton("Fill Median/Mode")
        self._fill_median.clicked.connect(self._fill_defaults)
        defaults_row.addWidget(self._fill_median)
        defaults_row.addStretch(1)
        opts_layout.addLayout(defaults_row)
        layout.addWidget(opts_group)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self._apply_button = QPushButton("Create")
        self._apply_button.setProperty("primary", True)
        self._apply_button.clicked.connect(self._apply)
        footer.addWidget(self._apply_button)
        layout.addLayout(footer)

    def set_input_payload(self, payload) -> None:
        if payload is None:
            self._dataset_handle = None
        elif payload.port_label == "Data":
            self._dataset_handle = payload.dataset
        self._rebuild_fields()

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        values = {name: edit.text() for name, edit in self._value_edits.items()}
        return {"values": values, "append": self._append_cb.isChecked()}

    def restore_node_state(self, payload: dict[str, object]) -> None:
        values = payload.get("values", {})
        if isinstance(values, dict):
            for name, val in values.items():
                if name in self._value_edits:
                    self._value_edits[name].setText(str(val))
        self._append_cb.setChecked(bool(payload.get("append", False)))

    def help_text(self) -> str:
        return "Create a single data instance by specifying values for each column."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/createinstance/"

    def _rebuild_fields(self) -> None:
        self._value_edits.clear()
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()

        if self._dataset_handle is None:
            self._dataset_label.setText("Dataset: none")
            return

        self._dataset_label.setText(f"Dataset: {self._dataset_handle.display_name}")

        for col in self._dataset_handle.domain.columns:
            row = QHBoxLayout()
            label = QLabel(f"{col.name} ({col.logical_type}):")
            label.setMinimumWidth(150)
            row.addWidget(label)
            edit = QLineEdit()
            edit.setPlaceholderText(f"{col.role}")
            row.addWidget(edit, 1)
            self._value_edits[col.name] = edit
            container = QWidget()
            container.setLayout(row)
            self._fields_layout.addWidget(container)

    def _fill_defaults(self) -> None:
        if self._dataset_handle is None:
            return
        defaults = self._service.get_defaults(self._dataset_handle)
        for name, val in defaults.items():
            if name in self._value_edits:
                self._value_edits[name].setText(val)

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        values = {}
        for name, edit in self._value_edits.items():
            text = edit.text().strip()
            values[name] = text if text else None

        self._output_dataset = self._service.create(
            self._dataset_handle,
            values=values,
            append_to_data=self._append_cb.isChecked(),
        )

        self._result_label.setText(f"Created instance. Output: {self._output_dataset.row_count} rows")
        self._notify_output_changed()
