from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.transpose_service import TransposeService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class TransposeScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = TransposeService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        names_group = QGroupBox("Output Column Names")
        names_layout = QVBoxLayout(names_group)
        names_layout.setContentsMargins(10, 10, 10, 10)
        names_layout.setSpacing(8)

        self._name_mode_group = QButtonGroup(self)
        self._radio_generic = QRadioButton("Generic (prefix)")
        self._radio_generic.setChecked(True)
        self._radio_from_col = QRadioButton("From column")
        self._name_mode_group.addButton(self._radio_generic, 0)
        self._name_mode_group.addButton(self._radio_from_col, 1)
        names_layout.addWidget(self._radio_generic)

        prefix_row = QHBoxLayout()
        prefix_row.addWidget(QLabel("Prefix:"))
        self._prefix_edit = QLineEdit("Feature")
        prefix_row.addWidget(self._prefix_edit)
        names_layout.addLayout(prefix_row)

        names_layout.addWidget(self._radio_from_col)

        col_row = QHBoxLayout()
        col_row.addWidget(QLabel("Column:"))
        self._column_combo = QComboBox()
        col_row.addWidget(self._column_combo, 1)
        names_layout.addLayout(col_row)

        layout.addWidget(names_group)

        meta_group = QGroupBox("Meta Column")
        meta_layout = QHBoxLayout(meta_group)
        meta_layout.setContentsMargins(10, 10, 10, 10)
        meta_layout.addWidget(QLabel("Name for original columns:"))
        self._auto_col_name = QLineEdit("column")
        meta_layout.addWidget(self._auto_col_name)
        layout.addWidget(meta_group)

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
        self._column_combo.clear()

        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
            for col in dataset.domain.columns:
                if col.logical_type in ("text", "categorical"):
                    self._column_combo.addItem(col.name)
        else:
            self._dataset_label.setText("Dataset: none")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "name_mode": self._name_mode_group.checkedId(),
            "prefix": self._prefix_edit.text(),
            "from_column": self._column_combo.currentText(),
            "auto_col_name": self._auto_col_name.text(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        mode_id = int(payload.get("name_mode", 0))
        btn = self._name_mode_group.button(mode_id)
        if btn:
            btn.setChecked(True)
        self._prefix_edit.setText(str(payload.get("prefix", "Feature")))
        col = str(payload.get("from_column", ""))
        if col and self._column_combo.findText(col) >= 0:
            self._column_combo.setCurrentText(col)
        self._auto_col_name.setText(str(payload.get("auto_col_name", "column")))

    def help_text(self) -> str:
        return "Transpose the dataset: flip rows and columns."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/transpose/"

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        from_col = None
        if self._name_mode_group.checkedId() == 1 and self._column_combo.currentText():
            from_col = self._column_combo.currentText()

        self._output_dataset = self._service.transpose(
            self._dataset_handle,
            feature_names_from=from_col,
            feature_name_prefix=self._prefix_edit.text() or "Feature",
            auto_column_name=self._auto_col_name.text() or "column",
        )

        self._result_label.setText(
            f"Result: {self._output_dataset.row_count} rows x {self._output_dataset.column_count} columns"
        )
        self._notify_output_changed()
