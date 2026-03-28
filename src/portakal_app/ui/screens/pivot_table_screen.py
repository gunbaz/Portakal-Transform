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
from portakal_app.data.services.pivot_table_service import PIVOT_AGGREGATIONS, PivotTableService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport
from portakal_app.ui.shared.type_icons import type_badge_icon


class PivotTableScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = PivotTableService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        settings_group = QGroupBox("Pivot Settings")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setSpacing(8)

        row_r = QHBoxLayout()
        row_r.addWidget(QLabel("Row:"))
        self._row_combo = QComboBox()
        row_r.addWidget(self._row_combo, 1)
        settings_layout.addLayout(row_r)

        col_r = QHBoxLayout()
        col_r.addWidget(QLabel("Column:"))
        self._col_combo = QComboBox()
        col_r.addWidget(self._col_combo, 1)
        settings_layout.addLayout(col_r)

        val_r = QHBoxLayout()
        val_r.addWidget(QLabel("Value:"))
        self._val_combo = QComboBox()
        self._val_combo.addItem("(Count)")
        val_r.addWidget(self._val_combo, 1)
        settings_layout.addLayout(val_r)

        agg_r = QHBoxLayout()
        agg_r.addWidget(QLabel("Aggregation:"))
        self._agg_combo = QComboBox()
        self._agg_combo.addItems(list(PIVOT_AGGREGATIONS))
        agg_r.addWidget(self._agg_combo, 1)
        settings_layout.addLayout(agg_r)

        layout.addWidget(settings_group)

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
        self._row_combo.clear()
        self._col_combo.clear()
        self._val_combo.clear()
        self._val_combo.addItem("(Count)")

        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
            for col in dataset.domain.columns:
                icon = type_badge_icon(col.logical_type)
                self._row_combo.addItem(icon, col.name)
                self._col_combo.addItem(icon, col.name)
                self._val_combo.addItem(icon, col.name)
        else:
            self._dataset_label.setText("Dataset: none")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "row": self._row_combo.currentText(),
            "col": self._col_combo.currentText(),
            "val": self._val_combo.currentText(),
            "agg": self._agg_combo.currentText(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        for key, combo in [("row", self._row_combo), ("col", self._col_combo), ("val", self._val_combo), ("agg", self._agg_combo)]:
            val = str(payload.get(key, ""))
            if val and combo.findText(val) >= 0:
                combo.setCurrentText(val)

    def help_text(self) -> str:
        return "Create a pivot (cross-tabulation) table from the dataset."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/pivottable/"

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        val = self._val_combo.currentText()
        value_col = None if val == "(Count)" else val

        self._output_dataset = self._service.pivot(
            self._dataset_handle,
            row_column=self._row_combo.currentText(),
            col_column=self._col_combo.currentText(),
            value_column=value_col,
            aggregation=self._agg_combo.currentText(),
        )

        self._result_label.setText(
            f"Pivot: {self._output_dataset.row_count} rows x {self._output_dataset.column_count} columns"
        )
        self._notify_output_changed()
