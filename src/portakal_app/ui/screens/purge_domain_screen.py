from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.purge_domain_service import PurgeDomainService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class PurgeDomainScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = PurgeDomainService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        features_group = QGroupBox("Features")
        features_layout = QVBoxLayout(features_group)
        features_layout.setContentsMargins(10, 10, 10, 10)
        features_layout.setSpacing(8)
        self._sort_features = QCheckBox("Sort feature values")
        self._sort_features.setChecked(True)
        features_layout.addWidget(self._sort_features)
        self._remove_unused_features = QCheckBox("Remove unused feature values")
        self._remove_unused_features.setChecked(True)
        features_layout.addWidget(self._remove_unused_features)
        self._remove_constant_features = QCheckBox("Remove constant features")
        self._remove_constant_features.setChecked(True)
        features_layout.addWidget(self._remove_constant_features)
        layout.addWidget(features_group)

        classes_group = QGroupBox("Classes")
        classes_layout = QVBoxLayout(classes_group)
        classes_layout.setContentsMargins(10, 10, 10, 10)
        classes_layout.setSpacing(8)
        self._sort_classes = QCheckBox("Sort class values")
        self._sort_classes.setChecked(True)
        classes_layout.addWidget(self._sort_classes)
        self._remove_unused_classes = QCheckBox("Remove unused class values")
        self._remove_unused_classes.setChecked(True)
        classes_layout.addWidget(self._remove_unused_classes)
        self._remove_constant_classes = QCheckBox("Remove constant class attributes")
        self._remove_constant_classes.setChecked(True)
        classes_layout.addWidget(self._remove_constant_classes)
        layout.addWidget(classes_group)

        metas_group = QGroupBox("Meta Attributes")
        metas_layout = QVBoxLayout(metas_group)
        metas_layout.setContentsMargins(10, 10, 10, 10)
        metas_layout.setSpacing(8)
        self._remove_unused_metas = QCheckBox("Remove unused meta values")
        self._remove_unused_metas.setChecked(True)
        metas_layout.addWidget(self._remove_unused_metas)
        self._remove_constant_metas = QCheckBox("Remove constant meta attributes")
        self._remove_constant_metas.setChecked(True)
        metas_layout.addWidget(self._remove_constant_metas)
        layout.addWidget(metas_group)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)

        self._stats_label = QLabel("No data processed yet.")
        self._stats_label.setWordWrap(True)
        layout.addWidget(self._stats_label)

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
            self._stats_label.setText("No data processed yet.")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "sort_features": self._sort_features.isChecked(),
            "remove_unused_features": self._remove_unused_features.isChecked(),
            "remove_constant_features": self._remove_constant_features.isChecked(),
            "sort_classes": self._sort_classes.isChecked(),
            "remove_unused_classes": self._remove_unused_classes.isChecked(),
            "remove_constant_classes": self._remove_constant_classes.isChecked(),
            "remove_unused_metas": self._remove_unused_metas.isChecked(),
            "remove_constant_metas": self._remove_constant_metas.isChecked(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        self._sort_features.setChecked(bool(payload.get("sort_features", True)))
        self._remove_unused_features.setChecked(bool(payload.get("remove_unused_features", True)))
        self._remove_constant_features.setChecked(bool(payload.get("remove_constant_features", True)))
        self._sort_classes.setChecked(bool(payload.get("sort_classes", True)))
        self._remove_unused_classes.setChecked(bool(payload.get("remove_unused_classes", True)))
        self._remove_constant_classes.setChecked(bool(payload.get("remove_constant_classes", True)))
        self._remove_unused_metas.setChecked(bool(payload.get("remove_unused_metas", True)))
        self._remove_constant_metas.setChecked(bool(payload.get("remove_constant_metas", True)))

    def help_text(self) -> str:
        return "Remove unused values, constant features, and sort categorical values from the dataset domain."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/purgedomain/"

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._stats_label.setText("No data processed yet.")
            self._notify_output_changed()
            return

        self._output_dataset, stats = self._service.purge(
            self._dataset_handle,
            remove_unused_features=self._remove_unused_features.isChecked(),
            remove_constant_features=self._remove_constant_features.isChecked(),
            sort_feature_values=self._sort_features.isChecked(),
            remove_unused_classes=self._remove_unused_classes.isChecked(),
            remove_constant_classes=self._remove_constant_classes.isChecked(),
            sort_class_values=self._sort_classes.isChecked(),
            remove_unused_metas=self._remove_unused_metas.isChecked(),
            remove_constant_metas=self._remove_constant_metas.isChecked(),
        )

        before = self._dataset_handle.column_count
        after = self._output_dataset.column_count
        self._stats_label.setText(
            f"Sorted: {stats['sorted']} | Removed: {stats['removed']} | "
            f"Columns: {before} -> {after}"
        )
        self._notify_output_changed()
