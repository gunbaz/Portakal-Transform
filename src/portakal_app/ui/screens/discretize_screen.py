from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.discretize_service import METHODS, DiscretizeService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class DiscretizeScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = DiscretizeService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        settings_group = QGroupBox("Discretization Settings")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setSpacing(8)

        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Method:"))
        self._method_combo = QComboBox()
        self._method_combo.addItems(list(METHODS))
        self._method_combo.setCurrentText("Equal Width")
        method_row.addWidget(self._method_combo, 1)
        settings_layout.addLayout(method_row)

        bins_row = QHBoxLayout()
        bins_row.addWidget(QLabel("Number of bins:"))
        self._bins_spin = QSpinBox()
        self._bins_spin.setRange(2, 50)
        self._bins_spin.setValue(4)
        bins_row.addWidget(self._bins_spin)
        bins_row.addStretch(1)
        settings_layout.addLayout(bins_row)

        layout.addWidget(settings_group)

        self._info_label = QLabel(
            "Converts numeric columns into categorical bins.\n"
            "Equal Width: bins of equal range.\n"
            "Equal Frequency: bins with equal number of instances.\n"
            "Remove: drops all numeric columns.\n"
            "Keep Numeric: no transformation."
        )
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet("color: gray;")
        layout.addWidget(self._info_label)

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
        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
        else:
            self._dataset_label.setText("Dataset: none")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "method": self._method_combo.currentText(),
            "n_bins": self._bins_spin.value(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        m = str(payload.get("method", "Equal Width"))
        if self._method_combo.findText(m) >= 0:
            self._method_combo.setCurrentText(m)
        self._bins_spin.setValue(int(payload.get("n_bins", 4)))

    def help_text(self) -> str:
        return "Discretize numeric columns into categorical bins using equal width or equal frequency methods."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/discretize/"

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        self._output_dataset = self._service.discretize(
            self._dataset_handle,
            method=self._method_combo.currentText(),
            n_bins=self._bins_spin.value(),
        )

        before = self._dataset_handle.column_count
        after = self._output_dataset.column_count
        self._result_label.setText(
            f"Discretized: {after} columns (was {before}) using {self._method_combo.currentText()}"
        )
        self._notify_output_changed()
