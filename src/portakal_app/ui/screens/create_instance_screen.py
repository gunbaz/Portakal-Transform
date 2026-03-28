from __future__ import annotations

from typing import Any
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.create_instance_service import CreateInstanceService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport
from portakal_app.ui import i18n

class CreateInstanceScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = CreateInstanceService()
        self._data_ds: DatasetHandle | None = None
        self._ref_ds: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None
        self._value_edits: dict[str, QLineEdit] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Filter...")
        self._filter_edit.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self._filter_edit)

        self._table = QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Variable", "Value"])
        header = self._table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        
        self._btn_median = QPushButton("Median")
        self._btn_median.clicked.connect(lambda: self._fill_defaults("median"))
        btn_row.addWidget(self._btn_median)
        
        self._btn_mean = QPushButton("Mean")
        self._btn_mean.clicked.connect(lambda: self._fill_defaults("mean"))
        btn_row.addWidget(self._btn_mean)
        
        self._btn_random = QPushButton("Random")
        self._btn_random.clicked.connect(lambda: self._fill_defaults("random"))
        btn_row.addWidget(self._btn_random)
        
        self._btn_input = QPushButton("Input")
        self._btn_input.clicked.connect(self._fill_from_input)
        btn_row.addWidget(self._btn_input)
        
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        bottom_row = QHBoxLayout()
        self._append_cb = QCheckBox("Append this instance to input data")
        self._append_cb.setChecked(True)
        self._append_cb.stateChanged.connect(self._check_auto_apply)
        bottom_row.addWidget(self._append_cb)
        
        bottom_row.addStretch(1)
        self._auto_apply_cb = QCheckBox("Apply Automatically")
        self._auto_apply_cb.setChecked(True)
        bottom_row.addWidget(self._auto_apply_cb)

        self._apply_button = QPushButton("Create")
        self._apply_button.setProperty("primary", True)
        self._apply_button.clicked.connect(self._apply)
        bottom_row.addWidget(self._apply_button)
        layout.addLayout(bottom_row)
        
        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

    def _check_auto_apply(self) -> None:
        if self._auto_apply_cb.isChecked():
            self._apply()

    def set_input_payload(self, payload) -> None:
        if payload is None:
            self._data_ds = None
            self._ref_ds = None
        else:
            if getattr(payload, "port_label", None) == "Data":
                self._data_ds = getattr(payload, "dataset", None)
            elif getattr(payload, "port_label", None) == "Reference":
                self._ref_ds = getattr(payload, "dataset", None)
        self._rebuild_fields()

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        values = {name: edit.text() for name, edit in self._value_edits.items()}
        return {
            "values": values, 
            "append": self._append_cb.isChecked(),
            "auto_apply": self._auto_apply_cb.isChecked()
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        values = payload.get("values", {})
        if isinstance(values, dict):
            for name, val in values.items():
                if name in self._value_edits:
                    self._value_edits[name].setText(str(val))
        self._append_cb.setChecked(bool(payload.get("append", True)))
        self._auto_apply_cb.setChecked(bool(payload.get("auto_apply", True)))

    def help_text(self) -> str:
        return "Create a single instance (row) by setting column values manually or automatically based on logic."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/createinstance/"

    def _get_schema_ds(self) -> DatasetHandle | None:
        return self._ref_ds if self._ref_ds is not None else self._data_ds

    def _rebuild_fields(self) -> None:
        # cache old values
        old_values = {name: edit.text() for name, edit in self._value_edits.items()}
        self._value_edits.clear()
        
        # update table
        self._table.setRowCount(0)
        
        schema_ds = self._get_schema_ds()
        if schema_ds is None:
            return

        cols = schema_ds.domain.columns
        self._table.setRowCount(len(cols))

        for idx, col in enumerate(cols):
            type_label = col.logical_type
            if type_label == "numeric":
                type_label = "Num"
            elif type_label == "categorical":
                type_label = "Cat"
            elif type_label == "text":
                type_label = "Txt"
            elif type_label == "datetime":
                type_label = "Time"
                
            var_item = QTableWidgetItem(f"{col.name} ({type_label})")
            # store actual name in user data to handle filtering logic
            var_item.setData(99, col.name) 
            self._table.setItem(idx, 0, var_item)
            
            edit = QLineEdit()
            edit.setPlaceholderText("value")
            # restore old value if any
            if col.name in old_values:
                edit.setText(old_values[col.name])
            edit.textChanged.connect(self._check_auto_apply)
            
            self._value_edits[col.name] = edit
            self._table.setCellWidget(idx, 1, edit)

        self._on_filter_changed()

    def _on_filter_changed(self) -> None:
        text = self._filter_edit.text().strip().lower()
        for idx in range(self._table.rowCount()):
            item = self._table.item(idx, 0)
            if not item:
                continue
            name = item.data(99) or ""
            if not text or text in name.lower() or text in item.text().lower():
                self._table.setRowHidden(idx, False)
            else:
                self._table.setRowHidden(idx, True)

    def _fill_defaults(self, stat_type: str) -> None:
        schema_ds = self._get_schema_ds()
        if schema_ds is None:
            return
            
        try:
            defaults = self._service.get_defaults(schema_ds, stat_type)
            for name, val in defaults.items():
                if name in self._value_edits:
                    self._value_edits[name].blockSignals(True)
                    self._value_edits[name].setText(val)
                    self._value_edits[name].blockSignals(False)
            self._check_auto_apply()
        except Exception:
            pass

    def _fill_from_input(self) -> None:
        schema_ds = self._get_schema_ds()
        if schema_ds is None or schema_ds.dataframe.height == 0:
            return
            
        first_row = schema_ds.dataframe.row(0, named=True)
        for name, edit in self._value_edits.items():
            if name in first_row:
                val = first_row[name]
                edit.blockSignals(True)
                edit.setText(str(val) if val is not None else "")
                edit.blockSignals(False)
                
        self._check_auto_apply()

    def _apply(self) -> None:
        schema_ds = self._get_schema_ds()
        if schema_ds is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        values = {}
        for name, edit in self._value_edits.items():
            text = edit.text().strip()
            values[name] = text if text else None

        try:
            self._output_dataset = self._service.create(
                reference=self._ref_ds,
                data=self._data_ds,
                values=values,
                append_to_data=self._append_cb.isChecked(),
            )
            self._result_label.setText(f"Created instance. Output: {self._output_dataset.row_count} rows")
        except Exception as e:
            self._output_dataset = None
            self._result_label.setText(f"Error creating instance: {e}")

        self._notify_output_changed()
