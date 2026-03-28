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
from portakal_app.ui import i18n


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

        # Dataset label
        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        # Features
        features_group = QGroupBox("Features")
        features_layout = QVBoxLayout(features_group)
        features_layout.setContentsMargins(10, 10, 10, 10)
        self._sort_features = QCheckBox("Sort categorical feature values")
        self._sort_features.setChecked(True)
        features_layout.addWidget(self._sort_features)
        
        self._remove_unused_features = QCheckBox("Remove unused feature values")
        self._remove_unused_features.setChecked(True)
        features_layout.addWidget(self._remove_unused_features)
        
        self._remove_constant_features = QCheckBox("Remove constant features")
        self._remove_constant_features.setChecked(True)
        features_layout.addWidget(self._remove_constant_features)

        features_sep = QFrame()
        features_sep.setFrameShape(QFrame.Shape.HLine)
        features_layout.addWidget(features_sep)

        self._features_stats = QLabel("Sorted: -, reduced: -, removed: -")
        features_layout.addWidget(self._features_stats)
        
        layout.addWidget(features_group)

        # Classes
        classes_group = QGroupBox("Classes")
        classes_layout = QVBoxLayout(classes_group)
        classes_layout.setContentsMargins(10, 10, 10, 10)
        self._sort_classes = QCheckBox("Sort categorical class values")
        self._sort_classes.setChecked(True)
        classes_layout.addWidget(self._sort_classes)
        
        self._remove_unused_classes = QCheckBox("Remove unused class variable values")
        self._remove_unused_classes.setChecked(True)
        classes_layout.addWidget(self._remove_unused_classes)
        
        self._remove_constant_classes = QCheckBox("Remove constant class variables")
        self._remove_constant_classes.setChecked(True)
        classes_layout.addWidget(self._remove_constant_classes)

        classes_sep = QFrame()
        classes_sep.setFrameShape(QFrame.Shape.HLine)
        classes_layout.addWidget(classes_sep)

        self._classes_stats = QLabel("Sorted: -, reduced: -, removed: -")
        classes_layout.addWidget(self._classes_stats)

        layout.addWidget(classes_group)

        # Meta attributes
        metas_group = QGroupBox("Meta attributes")
        metas_layout = QVBoxLayout(metas_group)
        metas_layout.setContentsMargins(10, 10, 10, 10)
        
        self._remove_unused_metas = QCheckBox("Remove unused meta attribute values")
        self._remove_unused_metas.setChecked(True)
        metas_layout.addWidget(self._remove_unused_metas)
        
        self._remove_constant_metas = QCheckBox("Remove constant meta attributes")
        self._remove_constant_metas.setChecked(True)
        metas_layout.addWidget(self._remove_constant_metas)

        metas_sep = QFrame()
        metas_sep.setFrameShape(QFrame.Shape.HLine)
        metas_layout.addWidget(metas_sep)

        self._metas_stats = QLabel("Reduced: -, removed: -")
        metas_layout.addWidget(self._metas_stats)

        layout.addWidget(metas_group)
        layout.addStretch(1)

        # Hook auto-apply signal to all checkboxes
        checkboxes = [
            self._sort_features, self._remove_unused_features, self._remove_constant_features,
            self._sort_classes, self._remove_unused_classes, self._remove_constant_classes,
            self._remove_unused_metas, self._remove_constant_metas
        ]
        for cb in checkboxes:
            cb.stateChanged.connect(self._check_auto_apply)

        footer = QHBoxLayout()
        self.cb_apply_auto = QCheckBox("Send Automatically")
        self.cb_apply_auto.setChecked(True)
        footer.addWidget(self.cb_apply_auto)
        
        footer.addStretch(1)
        self._apply_button = QPushButton("Send") # Orange actually calls this Send or Apply depending.
        self._apply_button.setProperty("primary", True)
        self._apply_button.clicked.connect(self._apply)
        footer.addWidget(self._apply_button)
        layout.addLayout(footer)

    def _check_auto_apply(self):
        if self.cb_apply_auto.isChecked():
            self._apply()

    def set_input_payload(self, payload) -> None:
        dataset = payload.dataset if payload is not None else None
        self._dataset_handle = dataset
        self._output_dataset = None
        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
        else:
            self._dataset_label.setText("Dataset: none")
            self._features_stats.setText("Sorted: -, reduced: -, removed: -")
            self._classes_stats.setText("Sorted: -, reduced: -, removed: -")
            self._metas_stats.setText("Reduced: -, removed: -")

        self._check_auto_apply()

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
            "auto_apply": self.cb_apply_auto.isChecked(),
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
        self.cb_apply_auto.setChecked(bool(payload.get("auto_apply", True)))

    def help_text(self) -> str:
        return "Remove unused values, constant features, and sort categorical values from the dataset domain."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/purgedomain/"

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._features_stats.setText("Sorted: -, reduced: -, removed: -")
            self._classes_stats.setText("Sorted: -, reduced: -, removed: -")
            self._metas_stats.setText("Reduced: -, removed: -")
            self._notify_output_changed()
            return

        try:
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
            fs = stats.get("features", {})
            self._features_stats.setText(f"Sorted: {fs.get('sorted', 0)}, reduced: {fs.get('reduced', 0)}, removed: {fs.get('removed', 0)}")
            cs = stats.get("classes", {})
            self._classes_stats.setText(f"Sorted: {cs.get('sorted', 0)}, reduced: {cs.get('reduced', 0)}, removed: {cs.get('removed', 0)}")
            ms = stats.get("metas", {})
            self._metas_stats.setText(f"Reduced: {ms.get('reduced', 0)}, removed: {ms.get('removed', 0)}")

        except Exception as e:
            self._features_stats.setText("Error applying purge.")
            self._output_dataset = None

        self._notify_output_changed()
