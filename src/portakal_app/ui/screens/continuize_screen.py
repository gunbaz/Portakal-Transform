from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.continuize_service import (
    CONTINUOUS_METHODS,
    DISCRETE_METHODS,
    ContinuizeService,
)
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class ContinuizeScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = ContinuizeService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        discrete_group = QGroupBox("Discrete Columns")
        discrete_layout = QVBoxLayout(discrete_group)
        discrete_layout.setContentsMargins(10, 10, 10, 10)
        discrete_layout.setSpacing(8)
        disc_row = QHBoxLayout()
        disc_row.addWidget(QLabel("Treatment:"))
        self._discrete_combo = QComboBox()
        self._discrete_combo.addItems(list(DISCRETE_METHODS))
        self._discrete_combo.setCurrentText("One-hot encoding")
        disc_row.addWidget(self._discrete_combo, 1)
        discrete_layout.addLayout(disc_row)
        layout.addWidget(discrete_group)

        continuous_group = QGroupBox("Continuous Columns")
        continuous_layout = QVBoxLayout(continuous_group)
        continuous_layout.setContentsMargins(10, 10, 10, 10)
        continuous_layout.setSpacing(8)
        cont_row = QHBoxLayout()
        cont_row.addWidget(QLabel("Normalization:"))
        self._continuous_combo = QComboBox()
        self._continuous_combo.addItems(list(CONTINUOUS_METHODS))
        self._continuous_combo.setCurrentText("Keep as is")
        cont_row.addWidget(self._continuous_combo, 1)
        continuous_layout.addLayout(cont_row)
        layout.addWidget(continuous_group)

        self._info_label = QLabel(
            "Converts categorical columns to numeric and optionally normalizes numeric columns.\n"
            "One-hot encoding creates a binary column for each category value."
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
            "discrete_method": self._discrete_combo.currentText(),
            "continuous_method": self._continuous_combo.currentText(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        dm = str(payload.get("discrete_method", "One-hot encoding"))
        if self._discrete_combo.findText(dm) >= 0:
            self._discrete_combo.setCurrentText(dm)
        cm = str(payload.get("continuous_method", "Keep as is"))
        if self._continuous_combo.findText(cm) >= 0:
            self._continuous_combo.setCurrentText(cm)

    def help_text(self) -> str:
        return "Convert categorical columns to numeric (one-hot, ordinal, etc.) and normalize continuous columns."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/continuize/"

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        self._output_dataset = self._service.continuize(
            self._dataset_handle,
            discrete_method=self._discrete_combo.currentText(),
            continuous_method=self._continuous_combo.currentText(),
        )

        before = self._dataset_handle.column_count
        after = self._output_dataset.column_count
        self._result_label.setText(f"Result: {after} columns (was {before})")
        self._notify_output_changed()
