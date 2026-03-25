from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.randomize_service import RandomizeService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class RandomizeScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = RandomizeService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        columns_group = QGroupBox("Shuffled Columns")
        columns_layout = QVBoxLayout(columns_group)
        columns_layout.setContentsMargins(10, 10, 10, 10)
        columns_layout.setSpacing(8)

        self._shuffle_classes = QCheckBox("Classes")
        self._shuffle_classes.setChecked(True)
        columns_layout.addWidget(self._shuffle_classes)

        self._shuffle_features = QCheckBox("Features")
        self._shuffle_features.setChecked(False)
        columns_layout.addWidget(self._shuffle_features)

        self._shuffle_metas = QCheckBox("Metas")
        self._shuffle_metas.setChecked(False)
        columns_layout.addWidget(self._shuffle_metas)

        layout.addWidget(columns_group)

        ratio_group = QGroupBox("Shuffled Rows")
        ratio_layout = QVBoxLayout(ratio_group)
        ratio_layout.setContentsMargins(10, 10, 10, 10)
        ratio_layout.setSpacing(8)

        slider_row = QHBoxLayout()
        self._ratio_slider = QSlider(Qt.Orientation.Horizontal)
        self._ratio_slider.setRange(0, 100)
        self._ratio_slider.setValue(100)
        self._ratio_slider.valueChanged.connect(self._on_ratio_changed)
        slider_row.addWidget(self._ratio_slider, 1)

        self._ratio_label = QLabel("100%")
        self._ratio_label.setMinimumWidth(40)
        slider_row.addWidget(self._ratio_label)
        ratio_layout.addLayout(slider_row)

        layout.addWidget(ratio_group)

        seed_group = QGroupBox("Reproducibility")
        seed_layout = QVBoxLayout(seed_group)
        seed_layout.setContentsMargins(10, 10, 10, 10)
        seed_layout.setSpacing(8)

        self._use_seed = QCheckBox("Use seed")
        self._use_seed.setChecked(True)
        seed_layout.addWidget(self._use_seed)

        seed_row = QHBoxLayout()
        seed_row.addWidget(QLabel("Seed:"))
        self._seed_spin = QSpinBox()
        self._seed_spin.setRange(0, 999999)
        self._seed_spin.setValue(42)
        seed_row.addWidget(self._seed_spin)
        seed_layout.addLayout(seed_row)

        layout.addWidget(seed_group)
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

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "shuffle_classes": self._shuffle_classes.isChecked(),
            "shuffle_features": self._shuffle_features.isChecked(),
            "shuffle_metas": self._shuffle_metas.isChecked(),
            "ratio": self._ratio_slider.value(),
            "use_seed": self._use_seed.isChecked(),
            "seed": self._seed_spin.value(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        self._shuffle_classes.setChecked(bool(payload.get("shuffle_classes", True)))
        self._shuffle_features.setChecked(bool(payload.get("shuffle_features", False)))
        self._shuffle_metas.setChecked(bool(payload.get("shuffle_metas", False)))
        self._ratio_slider.setValue(int(payload.get("ratio", 100)))
        self._use_seed.setChecked(bool(payload.get("use_seed", True)))
        self._seed_spin.setValue(int(payload.get("seed", 42)))

    def help_text(self) -> str:
        return "Randomize (shuffle) the order of rows, columns, or values in the dataset."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/randomize/"

    def _on_ratio_changed(self, value: int) -> None:
        self._ratio_label.setText(f"{value}%")

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._notify_output_changed()
            return

        seed = self._seed_spin.value() if self._use_seed.isChecked() else None
        self._output_dataset = self._service.randomize(
            self._dataset_handle,
            shuffle_classes=self._shuffle_classes.isChecked(),
            shuffle_features=self._shuffle_features.isChecked(),
            shuffle_metas=self._shuffle_metas.isChecked(),
            shuffle_ratio=self._ratio_slider.value(),
            seed=seed,
        )
        self._notify_output_changed()
