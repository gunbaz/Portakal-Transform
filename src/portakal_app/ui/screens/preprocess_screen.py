from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.preprocess_service import STEPS, PreprocessService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class PreprocessScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = PreprocessService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        steps_group = QGroupBox("Preprocessing Steps")
        steps_layout = QVBoxLayout(steps_group)
        steps_layout.setContentsMargins(10, 10, 10, 10)
        steps_layout.setSpacing(6)

        self._step_checks: dict[str, QCheckBox] = {}
        for step in STEPS:
            cb = QCheckBox(step)
            self._step_checks[step] = cb
            steps_layout.addWidget(cb)
        layout.addWidget(steps_group)

        threshold_group = QGroupBox("Parameters")
        threshold_layout = QHBoxLayout(threshold_group)
        threshold_layout.setContentsMargins(10, 10, 10, 10)
        threshold_layout.addWidget(QLabel("Missing threshold:"))
        self._threshold_spin = QDoubleSpinBox()
        self._threshold_spin.setRange(0.0, 1.0)
        self._threshold_spin.setSingleStep(0.05)
        self._threshold_spin.setValue(0.5)
        threshold_layout.addWidget(self._threshold_spin)
        layout.addWidget(threshold_group)

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
        steps = [name for name, cb in self._step_checks.items() if cb.isChecked()]
        return {"steps": steps, "threshold": self._threshold_spin.value()}

    def restore_node_state(self, payload: dict[str, object]) -> None:
        steps = payload.get("steps", [])
        if isinstance(steps, list):
            for name, cb in self._step_checks.items():
                cb.setChecked(name in steps)
        self._threshold_spin.setValue(float(payload.get("threshold", 0.5)))

    def help_text(self) -> str:
        return "Build a preprocessing pipeline: remove missing values, constant features, normalize, or standardize."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/preprocess/"

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        selected_steps = [name for name, cb in self._step_checks.items() if cb.isChecked()]

        self._output_dataset = self._service.preprocess(
            self._dataset_handle,
            steps=selected_steps,
            missing_threshold=self._threshold_spin.value(),
        )

        before_r = self._dataset_handle.row_count
        before_c = self._dataset_handle.column_count
        after_r = self._output_dataset.row_count
        after_c = self._output_dataset.column_count
        self._result_label.setText(
            f"Before: {before_r}r x {before_c}c  ->  After: {after_r}r x {after_c}c"
        )
        self._notify_output_changed()
