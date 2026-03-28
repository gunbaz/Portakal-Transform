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
from portakal_app.data.services.select_by_index_service import SelectByIndexService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class SelectByIndexScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = SelectByIndexService()
        self._dataset_handle: DatasetHandle | None = None
        self._subset_handle: DatasetHandle | None = None
        self._output_matching: DatasetHandle | None = None
        self._output_non_matching: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Data: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        info_group = QGroupBox("Info")
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(8)

        self._desc_label = QLabel(
            "Data rows keep their identity even when some or all original variables "
            "are replaced by variables computed from the original ones.\n\n"
            "This widget gets two data tables (\"Data\" and \"Data Subset\") that "
            "can be traced back to the same source. It selects all rows from Data "
            "that appear in Data Subset, based on row identity and not actual data."
        )
        self._desc_label.setWordWrap(True)
        info_layout.addWidget(self._desc_label)

        self._data_info = QLabel("Data: -")
        info_layout.addWidget(self._data_info)

        self._subset_info = QLabel("Data Subset: -")
        info_layout.addWidget(self._subset_info)

        self._result_info = QLabel("Matching: -  |  Non-matching: -  |  Total: -")
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
            self._subset_handle = None
        elif payload.port_label == "Data":
            self._dataset_handle = payload.dataset
        elif payload.port_label == "Data Subset":
            self._subset_handle = payload.dataset
        self._update_info()
        # Auto-apply when both inputs are available
        if self._dataset_handle is not None and self._subset_handle is not None:
            self._apply()

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_matching

    def current_output_datasets(self) -> dict[str, DatasetHandle | None] | None:
        return {
            "Matching Data": self._output_matching,
            "Non-matching Data": self._output_non_matching,
        }

    def serialize_node_state(self) -> dict[str, object]:
        return {}

    def restore_node_state(self, payload: dict[str, object]) -> None:
        pass

    def help_text(self) -> str:
        return "Select rows from the primary dataset based on indices present in a data subset."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/selectbydataindex/"

    def _update_info(self) -> None:
        if self._dataset_handle:
            self._dataset_label.setText(f"Data: {self._dataset_handle.display_name}")
            self._data_info.setText(f"Data: {self._dataset_handle.row_count} rows, {self._dataset_handle.column_count} columns")
        else:
            self._dataset_label.setText("Data: none")
            self._data_info.setText("Data: -")

        if self._subset_handle:
            self._subset_info.setText(f"Data Subset: {self._subset_handle.row_count} rows")
        else:
            self._subset_info.setText("Data Subset: -")

    def _apply(self) -> None:
        if self._dataset_handle is None or self._subset_handle is None:
            self._output_matching = None
            self._output_non_matching = None
            self._result_info.setText("Matching: -  |  Non-matching: -  |  Total: -")
            self._notify_output_changed()
            return

        matching, non_matching = self._service.select(self._dataset_handle, self._subset_handle)
        self._output_matching = matching
        self._output_non_matching = non_matching

        m_count = matching.row_count if matching else 0
        nm_count = non_matching.row_count if non_matching else 0
        total = self._dataset_handle.row_count
        self._result_info.setText(f"Matching: {m_count}  |  Non-matching: {nm_count}  |  Total: {total}")
        self._notify_output_changed()
