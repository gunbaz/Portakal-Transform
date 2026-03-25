from __future__ import annotations

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.apply_domain_service import ApplyDomainService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class ApplyDomainScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = ApplyDomainService()
        self._dataset_handle: DatasetHandle | None = None
        self._template_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Data: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        info_group = QGroupBox("Apply Domain")
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(8)

        self._desc_label = QLabel(
            "Apply the domain (column structure, roles, and types) from a Template dataset "
            "onto the input Data.\n\n"
            "Columns present in the template but missing in the data will be filled with null values. "
            "Columns in the data but not in the template will be dropped."
        )
        self._desc_label.setWordWrap(True)
        info_layout.addWidget(self._desc_label)

        self._data_info = QLabel("Data: -")
        info_layout.addWidget(self._data_info)

        self._template_info = QLabel("Template: -")
        info_layout.addWidget(self._template_info)

        self._result_info = QLabel("Output: -")
        info_layout.addWidget(self._result_info)

        layout.addWidget(info_group)
        layout.addStretch(1)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self._apply_button = QPushButton("Apply")
        self._apply_button.setProperty("primary", True)
        self._apply_button.clicked.connect(self._apply)
        footer.addWidget(self._apply_button)
        layout.addLayout(footer)

    def set_input_payload(self, payload) -> None:
        if payload is None:
            self._dataset_handle = None
            self._template_handle = None
        elif payload.port_label == "Data":
            self._dataset_handle = payload.dataset
        elif payload.port_label == "Template Data":
            self._template_handle = payload.dataset
        self._update_info()

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {}

    def restore_node_state(self, payload: dict[str, object]) -> None:
        pass

    def help_text(self) -> str:
        return "Apply the domain structure from a template dataset onto the input data."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/apply-domain/"

    def _update_info(self) -> None:
        if self._dataset_handle:
            self._dataset_label.setText(f"Data: {self._dataset_handle.display_name}")
            self._data_info.setText(
                f"Data: {self._dataset_handle.row_count} rows, {self._dataset_handle.column_count} columns"
            )
        else:
            self._dataset_label.setText("Data: none")
            self._data_info.setText("Data: -")

        if self._template_handle:
            self._template_info.setText(
                f"Template: {self._template_handle.display_name} "
                f"({self._template_handle.column_count} columns)"
            )
        else:
            self._template_info.setText("Template: -")

    def _apply(self) -> None:
        if self._dataset_handle is None or self._template_handle is None:
            self._output_dataset = None
            self._result_info.setText("Output: -")
            self._notify_output_changed()
            return

        self._output_dataset = self._service.apply(self._dataset_handle, self._template_handle)
        self._result_info.setText(
            f"Output: {self._output_dataset.row_count} rows, {self._output_dataset.column_count} columns"
        )
        self._notify_output_changed()
