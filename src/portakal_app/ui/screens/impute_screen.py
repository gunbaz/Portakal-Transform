from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.impute_service import METHODS, ImputeService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class ImputeScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = ImputeService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        method_group = QGroupBox("Imputation Method")
        method_layout = QVBoxLayout(method_group)
        method_layout.setContentsMargins(10, 10, 10, 10)
        method_layout.setSpacing(8)

        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Method:"))
        self._method_combo = QComboBox()
        self._method_combo.addItems(list(METHODS))
        self._method_combo.setCurrentText("Average/Most frequent")
        method_row.addWidget(self._method_combo, 1)
        method_layout.addLayout(method_row)

        fixed_row = QHBoxLayout()
        fixed_row.addWidget(QLabel("Fixed value:"))
        self._fixed_edit = QLineEdit("0")
        fixed_row.addWidget(self._fixed_edit, 1)
        method_layout.addLayout(fixed_row)

        seed_row = QHBoxLayout()
        seed_row.addWidget(QLabel("Seed:"))
        self._seed_spin = QSpinBox()
        self._seed_spin.setRange(0, 999999)
        self._seed_spin.setValue(42)
        seed_row.addWidget(self._seed_spin)
        method_layout.addLayout(seed_row)

        layout.addWidget(method_group)

        self._missing_info = QLabel("")
        self._missing_info.setWordWrap(True)
        layout.addWidget(self._missing_info)

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
            total_missing = sum(col.null_count for col in dataset.domain.columns)
            cols_with_missing = sum(1 for col in dataset.domain.columns if col.null_count > 0)
            self._missing_info.setText(
                f"Missing values: {total_missing} in {cols_with_missing} column(s)"
            )
        else:
            self._dataset_label.setText("Dataset: none")
            self._missing_info.setText("")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "method": self._method_combo.currentText(),
            "fixed_value": self._fixed_edit.text(),
            "seed": self._seed_spin.value(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        m = str(payload.get("method", "Average/Most frequent"))
        if self._method_combo.findText(m) >= 0:
            self._method_combo.setCurrentText(m)
        self._fixed_edit.setText(str(payload.get("fixed_value", "0")))
        self._seed_spin.setValue(int(payload.get("seed", 42)))

    def help_text(self) -> str:
        return "Fill missing values using average, fixed value, random sampling, or drop rows."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/impute/"

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        self._output_dataset = self._service.impute(
            self._dataset_handle,
            method=self._method_combo.currentText(),
            fixed_value=self._fixed_edit.text(),
            seed=self._seed_spin.value(),
        )

        remaining = sum(col.null_count for col in self._output_dataset.domain.columns)
        self._result_label.setText(
            f"Imputed. Remaining missing: {remaining} | Rows: {self._output_dataset.row_count}"
        )
        self._notify_output_changed()
