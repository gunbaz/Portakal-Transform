from __future__ import annotations

from typing import Any
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.formula_service import FormulaService, _SAFE_MATH, _SAFE_BUILTINS
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport
from portakal_app.ui import i18n

class FormulaScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = FormulaService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None
        
        self._formula_data: list[dict[str, object]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Dataset Label
        self._dataset_label = QLabel(i18n.t("Dataset: none"))
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        # Variable Definitions Top Area
        definitions_group = QGroupBox(i18n.t("Variable Definitions"))
        definitions_layout = QHBoxLayout(definitions_group)
        definitions_layout.setContentsMargins(10, 10, 10, 10)
        definitions_layout.setSpacing(10)

        # Left Buttons
        left_btn_layout = QVBoxLayout()
        self._new_btn = QPushButton(i18n.t("New"))
        self._new_btn.clicked.connect(self._add_new)
        left_btn_layout.addWidget(self._new_btn)

        self._remove_btn = QPushButton(i18n.t("Remove"))
        self._remove_btn.clicked.connect(self._remove_current)
        left_btn_layout.addWidget(self._remove_btn)
        left_btn_layout.addStretch(1)
        definitions_layout.addLayout(left_btn_layout)

        # Right Editors
        right_editor_layout = QVBoxLayout()
        top_row = QHBoxLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText(i18n.t("Name..."))
        self._name_edit.textEdited.connect(self._on_editor_changed)
        top_row.addWidget(self._name_edit, 1)

        self._expr_edit = QLineEdit()
        self._expr_edit.setPlaceholderText(i18n.t("Expression..."))
        self._expr_edit.textEdited.connect(self._on_editor_changed)
        top_row.addWidget(self._expr_edit, 3)
        right_editor_layout.addLayout(top_row)

        bottom_row = QHBoxLayout()
        self._meta_check = QCheckBox(i18n.t("Meta attribute"))
        self._meta_check.stateChanged.connect(self._on_editor_changed)
        bottom_row.addWidget(self._meta_check)

        self._col_combo = QComboBox()
        self._col_combo.addItem(i18n.t("Select Column"))
        self._col_combo.activated.connect(self._on_col_selected)
        bottom_row.addWidget(self._col_combo, 1)

        self._func_combo = QComboBox()
        self._func_combo.addItem(i18n.t("Select Function"))
        all_funcs = sorted(list(_SAFE_MATH.keys()) + list(_SAFE_BUILTINS.keys()))
        self._func_combo.addItems(all_funcs)
        self._func_combo.activated.connect(self._on_func_selected)
        bottom_row.addWidget(self._func_combo, 1)
        
        right_editor_layout.addLayout(bottom_row)
        definitions_layout.addLayout(right_editor_layout, 1)

        layout.addWidget(definitions_group)

        # Formula List
        self._list_widget = QListWidget()
        self._list_widget.currentRowChanged.connect(self._on_list_selection)
        layout.addWidget(self._list_widget, 1)

        # Result State
        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        # Bottom Send Button
        self._apply_button = QPushButton(i18n.t("Send"))
        self._apply_button.setProperty("primary", True)
        self._apply_button.clicked.connect(self._apply)
        # To mimic Orange's full width button, we just add it to layout directly
        layout.addWidget(self._apply_button)

        self._update_editor_state()

    def _update_editor_state(self):
        has_sel = self._list_widget.currentRow() >= 0
        self._name_edit.setEnabled(has_sel)
        self._expr_edit.setEnabled(has_sel)
        self._meta_check.setEnabled(has_sel)
        self._remove_btn.setEnabled(has_sel)
        self._col_combo.setEnabled(has_sel)
        self._func_combo.setEnabled(has_sel)

    def _render_list_items(self):
        current_row = self._list_widget.currentRow()
        self._list_widget.blockSignals(True)
        self._list_widget.clear()
        for idx, formula in enumerate(self._formula_data):
            name = formula.get("name", "New variables").strip()
            expr = formula.get("expr", "").strip()
            if not name:
                name = "New variables"
            display_str = f"{name} := {expr}" if expr else name
            item = QListWidgetItem(display_str)
            self._list_widget.addItem(item)
        
        if current_row >= 0 and current_row < self._list_widget.count():
            self._list_widget.setCurrentRow(current_row)
        
        self._list_widget.blockSignals(False)
        self._update_editor_state()

    def _add_new(self):
        self._formula_data.append({"name": "New variable", "expr": "", "is_meta": False})
        self._render_list_items()
        self._list_widget.setCurrentRow(len(self._formula_data) - 1)
        self._name_edit.setFocus()

    def _remove_current(self):
        row = self._list_widget.currentRow()
        if row >= 0 and row < len(self._formula_data):
            del self._formula_data[row]
            self._render_list_items()
            if self._formula_data:
                self._list_widget.setCurrentRow(min(row, len(self._formula_data) - 1))
            else:
                self._name_edit.clear()
                self._expr_edit.clear()
                self._meta_check.setChecked(False)

    def _on_list_selection(self, row: int):
        if row < 0 or row >= len(self._formula_data):
            self._update_editor_state()
            return
            
        data = self._formula_data[row]
        self._name_edit.blockSignals(True)
        self._expr_edit.blockSignals(True)
        self._meta_check.blockSignals(True)
        
        self._name_edit.setText(str(data.get("name", "")))
        self._expr_edit.setText(str(data.get("expr", "")))
        self._meta_check.setChecked(bool(data.get("is_meta", False)))
        
        self._name_edit.blockSignals(False)
        self._expr_edit.blockSignals(False)
        self._meta_check.blockSignals(False)
        self._update_editor_state()

    def _on_editor_changed(self):
        row = self._list_widget.currentRow()
        if row < 0 or row >= len(self._formula_data):
            return
            
        self._formula_data[row] = {
            "name": self._name_edit.text(),
            "expr": self._expr_edit.text(),
            "is_meta": self._meta_check.isChecked()
        }
        self._render_list_items()

    def _on_col_selected(self, index: int):
        if index > 0:
            col_name = self._col_combo.itemData(index) or self._col_combo.itemText(index)
            safe_name = col_name.replace(" ", "_").replace("-", "_")
            self._expr_edit.insert(safe_name)
            self._col_combo.setCurrentIndex(0)
            self._on_editor_changed()

    def _on_func_selected(self, index: int):
        if index > 0:
            text = self._func_combo.itemText(index)
            self._expr_edit.insert(f"{text}()")
            # Move cursor backwards into parenthesis
            cursor = self._expr_edit.cursorPosition()
            self._expr_edit.setCursorPosition(cursor - 1)
            self._func_combo.setCurrentIndex(0)
            self._on_editor_changed()

    def set_input_payload(self, payload) -> None:
        dataset = payload.dataset if payload is not None else None
        self._dataset_handle = dataset
        self._output_dataset = None
        
        self._col_combo.blockSignals(True)
        self._col_combo.clear()
        self._col_combo.addItem(i18n.t("Select Column"))

        if dataset:
            self._dataset_label.setText(i18n.tf("Dataset: {name}", name=dataset.display_name))
            for col in dataset.domain.columns:
                type_label = col.logical_type
                if type_label == "numeric":
                    type_label = "Num"
                elif type_label == "categorical":
                    type_label = "Cat"
                elif type_label == "text":
                    type_label = "Txt"
                elif type_label == "datetime":
                    type_label = "Time"
                self._col_combo.addItem(f"{col.name} ({type_label})", userData=col.name)
        else:
            self._dataset_label.setText(i18n.t("Dataset: none"))
            self._result_label.setText("")
            
        self._col_combo.blockSignals(False)

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {"formulas": self._formula_data}

    def restore_node_state(self, payload: dict[str, object]) -> None:
        raw_formulas = payload.get("formulas", [])
        self._formula_data.clear()
        
        if isinstance(raw_formulas, list):
            for item in raw_formulas:
                if isinstance(item, list) or isinstance(item, tuple):
                    # legacy portakal save compatibility `["name", "expr"]`
                    if len(item) == 2:
                        self._formula_data.append({"name": item[0], "expr": item[1], "is_meta": False})
                elif isinstance(item, dict):
                    self._formula_data.append({
                        "name": str(item.get("name", "")),
                        "expr": str(item.get("expr", "")),
                        "is_meta": bool(item.get("is_meta", False)),
                    })
                    
        self._render_list_items()
        if self._formula_data:
            self._list_widget.setCurrentRow(0)

    def help_text(self) -> str:
        return "Construct new features using mathematical or string expressions."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/featureconstructor/"

    def refresh_translations(self) -> None:
        if self._dataset_handle is None:
            self._dataset_label.setText(i18n.t("Dataset: none"))
        else:
            self._dataset_label.setText(i18n.tf("Dataset: {name}", name=self._dataset_handle.display_name))
        if self._output_dataset is not None and self._dataset_handle is not None:
            formulas = [f for f in self._formula_data if f.get("name") and f.get("expr")]
            new_cols = self._output_dataset.column_count - self._dataset_handle.column_count
            self._result_label.setText(
                i18n.tf(
                    "Applied {count} formula(s). New columns: {new_cols}. Output: {rows}r x {cols}c",
                    count=len(formulas), new_cols=new_cols,
                    rows=self._output_dataset.row_count, cols=self._output_dataset.column_count,
                )
            )

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        formulas = [f for f in self._formula_data if f.get("name") and f.get("expr")]

        try:
            self._output_dataset = self._service.apply_formulas(
                self._dataset_handle,
                formulas=formulas,
            )
            
            new_cols = self._output_dataset.column_count - self._dataset_handle.column_count
            self._result_label.setText(
                i18n.tf(
                    "Applied {count} formula(s). New columns: {new_cols}. Output: {rows}r x {cols}c",
                    count=len(formulas), new_cols=new_cols,
                    rows=self._output_dataset.row_count, cols=self._output_dataset.column_count,
                )
            )
        except Exception as e:
            self._output_dataset = None
            self._result_label.setText(i18n.tf("Formula Error: {error}", error=e))

        self._notify_output_changed()
