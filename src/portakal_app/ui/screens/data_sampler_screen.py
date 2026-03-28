from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.data_sampler_service import DataSamplerService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class DataSamplerScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = DataSamplerService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None
        self._remaining_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        # --- Sampling Type ---
        mode_group = QGroupBox("Sampling Type")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setContentsMargins(10, 10, 10, 10)
        mode_layout.setSpacing(8)

        self._mode_group = QButtonGroup(self)

        # 1. Fixed proportion
        self._radio_pct = QRadioButton("Fixed proportion of data:")
        self._radio_pct.setChecked(True)
        self._mode_group.addButton(self._radio_pct, 0)
        mode_layout.addWidget(self._radio_pct)

        pct_layout = QHBoxLayout()
        pct_layout.setContentsMargins(24, 0, 0, 4)
        pct_layout.setSpacing(8)
        self._pct_slider = QSlider(Qt.Orientation.Horizontal)
        self._pct_slider.setRange(1, 99)
        self._pct_slider.setValue(70)
        self._pct_slider.valueChanged.connect(self._on_pct_changed)
        pct_layout.addWidget(self._pct_slider, 1)
        self._pct_label = QLabel("70 %")
        self._pct_label.setMinimumWidth(40)
        pct_layout.addWidget(self._pct_label)
        mode_layout.addLayout(pct_layout)

        # 2. Fixed sample size
        self._radio_fixed = QRadioButton("Fixed sample size")
        self._mode_group.addButton(self._radio_fixed, 1)
        mode_layout.addWidget(self._radio_fixed)

        fixed_layout = QVBoxLayout()
        fixed_layout.setContentsMargins(24, 0, 0, 4)
        fixed_layout.setSpacing(4)
        
        fixed_row = QHBoxLayout()
        fixed_row.setContentsMargins(0, 0, 0, 0)
        fixed_row.addWidget(QLabel("Instances:"))
        self._fixed_spin = QSpinBox()
        self._fixed_spin.setRange(1, 999999)
        self._fixed_spin.setValue(30)
        fixed_row.addWidget(self._fixed_spin)
        fixed_row.addStretch(1)
        fixed_layout.addLayout(fixed_row)

        self._replacement_cb = QCheckBox("Sample with replacement")
        fixed_layout.addWidget(self._replacement_cb)
        mode_layout.addLayout(fixed_layout)

        # 3. Cross validation
        self._radio_cv = QRadioButton("Cross validation")
        self._mode_group.addButton(self._radio_cv, 2)
        mode_layout.addWidget(self._radio_cv)

        cv_layout = QVBoxLayout()
        cv_layout.setContentsMargins(24, 0, 0, 4)
        cv_layout.setSpacing(4)

        folds_row = QHBoxLayout()
        folds_row.setContentsMargins(0, 0, 0, 0)
        folds_row.addWidget(QLabel("Number of subsets:"))
        self._folds_spin = QSpinBox()
        self._folds_spin.setRange(2, 20)
        self._folds_spin.setValue(5)
        folds_row.addWidget(self._folds_spin)
        folds_row.addStretch(1)
        cv_layout.addLayout(folds_row)

        fold_row = QHBoxLayout()
        fold_row.setContentsMargins(0, 0, 0, 0)
        fold_row.addWidget(QLabel("Unused subset:"))
        self._fold_spin = QSpinBox()
        self._fold_spin.setRange(1, 20)
        self._fold_spin.setValue(1)
        fold_row.addWidget(self._fold_spin)
        fold_row.addStretch(1)
        cv_layout.addLayout(fold_row)

        mode_layout.addLayout(cv_layout)

        # 4. Bootstrap
        self._radio_bootstrap = QRadioButton("Bootstrap")
        self._mode_group.addButton(self._radio_bootstrap, 3)
        mode_layout.addWidget(self._radio_bootstrap)

        layout.addWidget(mode_group)

        # --- Options (Reproducibility & Stratify) ---
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        options_layout.setContentsMargins(10, 10, 10, 10)
        options_layout.setSpacing(8)

        self._use_seed = QCheckBox("Replicable (deterministic) sampling")
        self._use_seed.setChecked(True)
        options_layout.addWidget(self._use_seed)

        self._seed_spin = QSpinBox()
        self._seed_spin.setRange(0, 999999)
        self._seed_spin.setValue(42)
        self._seed_spin.setVisible(False)

        self._stratify_cb = QCheckBox("Stratify sample (when possible)")
        options_layout.addWidget(self._stratify_cb)

        layout.addWidget(options_group)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        layout.addStretch(1)

        self._apply_button = QPushButton("Sample Data")
        self._apply_button.setProperty("primary", True)
        self._apply_button.clicked.connect(self._apply)
        layout.addWidget(self._apply_button)

    def set_input_payload(self, payload) -> None:
        dataset = payload.dataset if payload is not None else None
        self._dataset_handle = dataset
        self._output_dataset = None
        self._remaining_dataset = None
        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
        else:
            self._dataset_label.setText("Dataset: none")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def current_output_datasets(self) -> dict[str, DatasetHandle | None] | None:
        return {
            "Data Sample": self._output_dataset,
            "Remaining Data": self._remaining_dataset,
        }

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "mode": self._mode_group.checkedId(),
            "percentage": self._pct_slider.value(),
            "fixed_size": self._fixed_spin.value(),
            "folds": self._folds_spin.value(),
            "selected_fold": self._fold_spin.value(),
            "replacement": self._replacement_cb.isChecked(),
            "stratify": self._stratify_cb.isChecked(),
            "use_seed": self._use_seed.isChecked(),
            "seed": self._seed_spin.value(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        mode_id = int(payload.get("mode", 0))
        btn = self._mode_group.button(mode_id)
        if btn:
            btn.setChecked(True)
        self._pct_slider.setValue(int(payload.get("percentage", 70)))
        self._fixed_spin.setValue(int(payload.get("fixed_size", 10)))
        self._folds_spin.setValue(int(payload.get("folds", 10)))
        self._fold_spin.setValue(int(payload.get("selected_fold", 1)))
        self._replacement_cb.setChecked(bool(payload.get("replacement", False)))
        self._stratify_cb.setChecked(bool(payload.get("stratify", False)))
        self._use_seed.setChecked(bool(payload.get("use_seed", True)))
        self._seed_spin.setValue(int(payload.get("seed", 42)))

    def help_text(self) -> str:
        return "Sample a subset of the data using fixed proportion, fixed size, cross-validation, or bootstrap."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/datasampler/"

    def _on_pct_changed(self, value: int) -> None:
        self._pct_label.setText(f"{value} %")

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._remaining_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        modes = {0: "percentage", 1: "fixed", 2: "cross-validation", 3: "bootstrap"}
        mode = modes.get(self._mode_group.checkedId(), "percentage")
        seed = self._seed_spin.value() if self._use_seed.isChecked() else None

        sample, remaining = self._service.sample(
            self._dataset_handle,
            mode=mode,
            percentage=self._pct_slider.value(),
            fixed_size=self._fixed_spin.value(),
            folds=self._folds_spin.value(),
            selected_fold=self._fold_spin.value(),
            with_replacement=self._replacement_cb.isChecked(),
            stratify=self._stratify_cb.isChecked(),
            seed=seed,
        )

        self._output_dataset = sample
        self._remaining_dataset = remaining
        s_count = sample.row_count if sample else 0
        r_count = remaining.row_count if remaining else 0
        self._result_label.setText(f"Sample: {s_count} rows  |  Remaining: {r_count} rows")
        self._notify_output_changed()
