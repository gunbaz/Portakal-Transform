from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QRectF

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.select_rows_service import (
    OPERATORS_CATEGORICAL,
    OPERATORS_NUMERIC,
    OPERATORS_STRING,
    SelectRowsService,
)
from portakal_app.ui import i18n
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport

def _create_type_icon(logical_type: str) -> QIcon:
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    if logical_type == "numeric":
        color = QColor("#ef4444")
        text = "N"
    elif logical_type in ("categorical", "boolean"):
        color = QColor("#22c55e")
        text = "C"
    elif logical_type in ("text", "string"):
        color = QColor("#8b5cf6")
        text = "S"
    elif logical_type in ("datetime", "date", "time"):
        color = QColor("#3b82f6")
        text = "D"
    else:
        color = QColor("#6b7280")
        text = "?"

    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, 16, 16, 3, 3)
    
    painter.setPen(QColor("white"))
    font = QFont("Arial", 9, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(QRectF(0, 0, 16, 16), Qt.AlignmentFlag.AlignCenter, text)
    painter.end()
    
    return QIcon(pixmap)


class _ConditionRow(QWidget):
    def __init__(self, columns: list[tuple[str, str, tuple[str, ...]]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._columns = {name: (ltype, samples) for name, ltype, samples in columns}

        self._col_combo = QComboBox()
        for name, ltype, _ in columns:
            self._col_combo.addItem(_create_type_icon(ltype), name)
            
        self._col_combo.currentTextChanged.connect(self._on_col_changed)
        layout.addWidget(self._col_combo, 1)

        self._op_combo = QComboBox()
        layout.addWidget(self._op_combo, 1)

        self._value_combo = QComboBox()
        self._value_combo.setEditable(True)
        layout.addWidget(self._value_combo, 1)

        self._remove_btn = QPushButton("x")
        self._remove_btn.setFixedWidth(30)
        layout.addWidget(self._remove_btn)

        self._on_col_changed(self._col_combo.currentText())

    def _on_col_changed(self, col_name: str) -> None:
        self._op_combo.clear()
        self._value_combo.clear()
        ltype, samples = self._columns.get(col_name, ("text", ()))
        
        if ltype in ("categorical", "boolean"):
            self._op_combo.addItems(list(OPERATORS_CATEGORICAL))
            self._value_combo.addItems(list(samples))
            self._value_combo.setEditable(False)
        elif ltype == "numeric":
            self._op_combo.addItems(list(OPERATORS_NUMERIC))
            self._value_combo.setEditable(True)
        else:
            self._op_combo.addItems(list(OPERATORS_STRING))
            self._value_combo.setEditable(True)

    def get_condition(self) -> tuple[str, str, str]:
        return (self._col_combo.currentText(), self._op_combo.currentText(), self._value_combo.currentText())


class SelectRowsScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = SelectRowsService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None
        self._unmatched_dataset: DatasetHandle | None = None
        self._condition_rows: list[_ConditionRow] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel(i18n.t("Dataset: none"))
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        cond_group = QGroupBox(i18n.t("Conditions"))
        self._cond_layout = QVBoxLayout(cond_group)
        self._cond_layout.setContentsMargins(10, 10, 10, 10)
        self._cond_layout.setSpacing(6)
        layout.addWidget(cond_group, 1)

        btn_row = QHBoxLayout()
        self._add_btn = QPushButton(i18n.t("+ Add Condition"))
        self._add_btn.clicked.connect(self._add_condition)
        btn_row.addWidget(self._add_btn)
        self._clear_btn = QPushButton(i18n.t("Remove All"))
        self._clear_btn.clicked.connect(self._clear_conditions)
        btn_row.addWidget(self._clear_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self._apply_button = QPushButton(i18n.t("Apply"))
        self._apply_button.setProperty("primary", True)
        self._apply_button.clicked.connect(self._apply)
        footer.addWidget(self._apply_button)
        layout.addLayout(footer)

    def set_input_payload(self, payload) -> None:
        dataset = payload.dataset if payload is not None else None
        self._dataset_handle = dataset
        self._output_dataset = None
        self._unmatched_dataset = None
        self._clear_conditions()

        if dataset:
            self._dataset_label.setText(i18n.tf("Dataset: {name}", name=dataset.display_name))
        else:
            self._dataset_label.setText(i18n.t("Dataset: none"))
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def current_output_datasets(self) -> dict[str, DatasetHandle | None] | None:
        return {
            "Matching Data": self._output_dataset,
            "Unmatched Data": self._unmatched_dataset,
        }

    def serialize_node_state(self) -> dict[str, object]:
        conditions = [row.get_condition() for row in self._condition_rows]
        return {"conditions": conditions}

    def restore_node_state(self, payload: dict[str, object]) -> None:
        pass

    def help_text(self) -> str:
        return "Filter rows using conditions on column values. Outputs matching and unmatched subsets."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/selectrows/"

    def _get_columns(self) -> list[tuple[str, str, tuple[str,...]]]:
        if self._dataset_handle is None:
            return []
        
        columns_data = []
        for col in self._dataset_handle.domain.columns:
            samples = ()
            if col.logical_type in ("categorical", "boolean"):
                series = self._dataset_handle.dataframe.get_column(col.name).drop_nulls()
                unique_vals = [str(x) for x in series.unique().to_list()]
                samples = tuple(sorted(unique_vals))
            columns_data.append((col.name, col.logical_type, samples))
        return columns_data

    def _add_condition(self) -> None:
        columns = self._get_columns()
        if not columns:
            return
        row = _ConditionRow(columns, self)
        row._remove_btn.clicked.connect(lambda: self._remove_condition(row))
        self._condition_rows.append(row)
        self._cond_layout.addWidget(row)

    def _remove_condition(self, row: _ConditionRow) -> None:
        if row in self._condition_rows:
            self._condition_rows.remove(row)
            self._cond_layout.removeWidget(row)
            row.deleteLater()

    def _clear_conditions(self) -> None:
        for row in self._condition_rows:
            self._cond_layout.removeWidget(row)
            row.deleteLater()
        self._condition_rows.clear()

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._unmatched_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        conditions = [row.get_condition() for row in self._condition_rows]
        matching, non_matching = self._service.filter_rows(
            self._dataset_handle,
            conditions=conditions,
        )

        self._output_dataset = matching
        self._unmatched_dataset = non_matching
        m = matching.row_count if matching else 0
        nm = non_matching.row_count if non_matching else 0
        self._result_label.setText(i18n.tf("Matching: {m}  |  Unmatched: {nm}", m=m, nm=nm))
        self._notify_output_changed()

    def refresh_translations(self) -> None:
        if self._dataset_handle is None:
            self._dataset_label.setText(i18n.t("Dataset: none"))
        else:
            self._dataset_label.setText(
                i18n.tf("Dataset: {name}", name=self._dataset_handle.display_name)
            )
        if self._output_dataset is not None:
            m = self._output_dataset.row_count
            nm = self._unmatched_dataset.row_count if self._unmatched_dataset else 0
            self._result_label.setText(
                i18n.tf("Matching: {m}  |  Unmatched: {nm}", m=m, nm=nm)
            )
