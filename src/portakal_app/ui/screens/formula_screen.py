from __future__ import annotations

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.formula_service import FormulaService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class _FormulaRow(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("New column name")
        layout.addWidget(self.name_edit, 1)

        self.expr_edit = QLineEdit()
        self.expr_edit.setPlaceholderText("Expression (e.g. col('x') + col('y'))")
        layout.addWidget(self.expr_edit, 2)

        self.remove_btn = QPushButton("x")
        self.remove_btn.setFixedWidth(30)
        layout.addWidget(self.remove_btn)

    def get_formula(self) -> tuple[str, str]:
        return (self.name_edit.text(), self.expr_edit.text())


class FormulaScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = FormulaService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None
        self._formula_rows: list[_FormulaRow] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        self._columns_label = QLabel("")
        self._columns_label.setWordWrap(True)
        layout.addWidget(self._columns_label)

        formulas_group = QGroupBox("Formulas (name -> expression)")
        formulas_outer = QVBoxLayout(formulas_group)
        formulas_outer.setContentsMargins(10, 10, 10, 10)
        formulas_outer.setSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._formulas_container = QWidget()
        self._formulas_layout = QVBoxLayout(self._formulas_container)
        self._formulas_layout.setContentsMargins(0, 0, 0, 0)
        self._formulas_layout.setSpacing(6)
        scroll.setWidget(self._formulas_container)
        formulas_outer.addWidget(scroll, 1)

        layout.addWidget(formulas_group, 1)

        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("+ Add Formula")
        self._add_btn.clicked.connect(self._add_formula)
        btn_row.addWidget(self._add_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        hint = QLabel(
            "Expressions use Polars syntax: col('name'), +, -, *, /, sqrt(), log(), etc."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(hint)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

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
            cols = [c.name for c in dataset.domain.columns]
            self._columns_label.setText(f"Columns: {', '.join(cols[:15])}")
        else:
            self._dataset_label.setText("Dataset: none")
            self._columns_label.setText("")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        formulas = [row.get_formula() for row in self._formula_rows]
        return {"formulas": formulas}

    def restore_node_state(self, payload: dict[str, object]) -> None:
        formulas = payload.get("formulas", [])
        if isinstance(formulas, list):
            for name, expr in formulas:
                self._add_formula()
                row = self._formula_rows[-1]
                row.name_edit.setText(str(name))
                row.expr_edit.setText(str(expr))

    def help_text(self) -> str:
        return "Construct new features using mathematical or string expressions on existing columns."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/featureconstructor/"

    def _add_formula(self) -> None:
        row = _FormulaRow(self)
        row.remove_btn.clicked.connect(lambda: self._remove_formula(row))
        self._formula_rows.append(row)
        self._formulas_layout.addWidget(row)

    def _remove_formula(self, row: _FormulaRow) -> None:
        if row in self._formula_rows:
            self._formula_rows.remove(row)
            self._formulas_layout.removeWidget(row)
            row.deleteLater()

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        formulas = [
            row.get_formula()
            for row in self._formula_rows
            if row.name_edit.text().strip() and row.expr_edit.text().strip()
        ]

        self._output_dataset = self._service.apply_formulas(
            self._dataset_handle,
            formulas=formulas,
        )

        new_cols = self._output_dataset.column_count - self._dataset_handle.column_count
        self._result_label.setText(
            f"Applied {len(formulas)} formula(s). New columns: {new_cols}. "
            f"Output: {self._output_dataset.row_count}r x {self._output_dataset.column_count}c"
        )
        self._notify_output_changed()
