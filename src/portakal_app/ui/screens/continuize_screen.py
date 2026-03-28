from __future__ import annotations

from typing import Any
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QRadioButton,
    QButtonGroup,
    QListWidgetItem,
    QCheckBox,
    QSplitter,
)
from PySide6.QtCore import Qt

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.continuize_service import (
    CONTINUOUS_METHODS,
    DISCRETE_METHODS,
    ContinuizeService,
)
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport
from portakal_app.ui import i18n


class TypeConfigurator(QGroupBox):
    def __init__(self, title: str, methods: tuple[str, ...], preset_initial: str, is_discrete: bool, parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        self.methods = methods
        self.is_discrete = is_discrete
        
        self.preset_value = preset_initial
        self.overrides: dict[str, str] = {}
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_list_change)
        layout.addWidget(self.list_widget, 1)
        
        right_panel = QVBoxLayout()
        self.group = QButtonGroup(self)
        self.radio_buttons: list[QRadioButton] = []
        for idx, method in enumerate(methods):
            rb = QRadioButton(method)
            self.group.addButton(rb, idx)
            self.radio_buttons.append(rb)
            right_panel.addWidget(rb)
            rb.clicked.connect(self._on_radio_change)
            
        right_panel.addStretch(1)
        layout.addLayout(right_panel, 1)

        self._populate_list([])

    def _populate_list(self, cols: list[str]) -> None:
        self.list_widget.clear()
        
        preset_item = QListWidgetItem(f"★ Preset: {self.preset_value}")
        preset_item.setData(Qt.ItemDataRole.UserRole, "__PRESET__")
        self.list_widget.addItem(preset_item)
        
        for col in cols:
            item = QListWidgetItem(col)
            item.setData(Qt.ItemDataRole.UserRole, col)
            self.list_widget.addItem(item)
            
        self.list_widget.setCurrentRow(0)

    def _on_list_change(self, row: int) -> None:
        if row < 0:
            return
            
        item = self.list_widget.item(row)
        col_id = item.data(Qt.ItemDataRole.UserRole)
        
        if col_id == "__PRESET__":
            self.radio_buttons[0].setEnabled(False) # 'Use preset' shouldn't be selected here
            val = self.preset_value
        else:
            self.radio_buttons[0].setEnabled(True)
            val = self.overrides.get(col_id, "Use preset")
            
        try:
            idx = self.methods.index(val)
            self.radio_buttons[idx].setChecked(True)
        except ValueError:
            pass

    def _on_radio_change(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0:
            return
            
        item = self.list_widget.item(row)
        col_id = item.data(Qt.ItemDataRole.UserRole)
        method_idx = self.group.checkedId()
        if method_idx < 0:
            return
            
        method = self.methods[method_idx]
        
        if col_id == "__PRESET__":
            if method == "Use preset":
                self.radio_buttons[1].setChecked(True) # Force change
                method = self.methods[1]
            self.preset_value = method
            item.setText(f"★ Preset: {method}")
        else:
            if method == "Use preset":
                if col_id in self.overrides:
                    del self.overrides[col_id]
            else:
                self.overrides[col_id] = method

    def reset_all(self):
        self.overrides.clear()
        self.list_widget.setCurrentRow(0)
        self._on_list_change(0)

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

        splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.cat_config = TypeConfigurator(
            "Categorical Variables", DISCRETE_METHODS, "First value as base", True
        )
        splitter.addWidget(self.cat_config)

        self.num_config = TypeConfigurator(
            "Numeric Variables", CONTINUOUS_METHODS, "Keep as it is", False
        )
        splitter.addWidget(self.num_config)
        
        layout.addWidget(splitter, 1)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        footer = QHBoxLayout()
        btn_reset = QPushButton("Reset All")
        btn_reset.clicked.connect(self._reset_all)
        footer.addWidget(btn_reset)
        
        footer.addStretch(1)
        self.cb_apply_auto = QCheckBox("Apply Automatically")
        self.cb_apply_auto.setChecked(True)
        footer.addWidget(self.cb_apply_auto)
        
        self._apply_button = QPushButton("Apply")
        self._apply_button.setProperty("primary", True)
        self._apply_button.clicked.connect(self._apply)
        footer.addWidget(self._apply_button)
        layout.addLayout(footer)

    def _reset_all(self):
        self.cat_config.reset_all()
        self.num_config.reset_all()
        if self.cb_apply_auto.isChecked():
            self._apply()

    def set_input_payload(self, payload) -> None:
        dataset = payload.dataset if payload is not None else None
        self._dataset_handle = dataset
        self._output_dataset = None
        
        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
            df = dataset.dataframe
            cat_cols = []
            num_cols = []
            for c in df.columns:
                dtype = df.get_column(c).dtype
                if dtype.is_numeric():
                    num_cols.append(c)
                elif dtype == pl.Utf8 or dtype == pl.Categorical:
                    cat_cols.append(c)
            self.cat_config._populate_list(cat_cols)
            self.num_config._populate_list(num_cols)
        else:
            self._dataset_label.setText("Dataset: none")
            self._result_label.setText("")
            self.cat_config._populate_list([])
            self.num_config._populate_list([])

        if self.cb_apply_auto.isChecked():
            self._apply()

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "discrete_preset": self.cat_config.preset_value,
            "continuous_preset": self.num_config.preset_value,
            "discrete_overrides": self.cat_config.overrides,
            "continuous_overrides": self.num_config.overrides,
            "auto_apply": self.cb_apply_auto.isChecked()
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        self.cat_config.preset_value = str(payload.get("discrete_preset", "First value as base"))
        self.num_config.preset_value = str(payload.get("continuous_preset", "Keep as it is"))
        
        self.cat_config.overrides = payload.get("discrete_overrides", {})
        self.num_config.overrides = payload.get("continuous_overrides", {})
        self.cb_apply_auto.setChecked(bool(payload.get("auto_apply", True)))

        # Update visuals for presets
        if self.cat_config.list_widget.count() > 0:
            self.cat_config.list_widget.item(0).setText(f"★ Preset: {self.cat_config.preset_value}")
        if self.num_config.list_widget.count() > 0:
            self.num_config.list_widget.item(0).setText(f"★ Preset: {self.num_config.preset_value}")

        self.cat_config._on_list_change(self.cat_config.list_widget.currentRow())
        self.num_config._on_list_change(self.num_config.list_widget.currentRow())

        if self.cb_apply_auto.isChecked():
            self._apply()

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
            
        all_methods = {}
        all_methods.update(self.cat_config.overrides)
        all_methods.update(self.num_config.overrides)

        try:
            self._output_dataset = self._service.continuize(
                self._dataset_handle,
                discrete_preset=self.cat_config.preset_value,
                continuous_preset=self.num_config.preset_value,
                column_methods=all_methods,
            )

            before = self._dataset_handle.column_count
            after = self._output_dataset.column_count
            self._result_label.setText(f"Result: {after} columns (was {before})")
        except Exception as e:
            self._output_dataset = None
            self._result_label.setText(f"Error: {e}")

        self._notify_output_changed()
