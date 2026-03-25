from __future__ import annotations

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
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.melt_service import MeltService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class MeltScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = MeltService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        settings_group = QGroupBox("Melt Settings")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setSpacing(8)

        id_row = QHBoxLayout()
        id_row.addWidget(QLabel("Row identifier:"))
        self._id_combo = QComboBox()
        self._id_combo.addItem("(Row number)")
        id_row.addWidget(self._id_combo, 1)
        settings_layout.addLayout(id_row)

        self._exclude_numeric = QCheckBox("Exclude numeric features")
        settings_layout.addWidget(self._exclude_numeric)

        self._exclude_zeros = QCheckBox("Exclude zero values")
        settings_layout.addWidget(self._exclude_zeros)

        names_row = QHBoxLayout()
        names_row.addWidget(QLabel("Item name:"))
        self._item_name = QLineEdit("item")
        names_row.addWidget(self._item_name)
        names_row.addWidget(QLabel("Value name:"))
        self._value_name = QLineEdit("value")
        names_row.addWidget(self._value_name)
        settings_layout.addLayout(names_row)

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
        self._id_combo.clear()
        self._id_combo.addItem("(Row number)")

        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
            for col in dataset.domain.columns:
                if col.logical_type in ("text", "categorical"):
                    self._id_combo.addItem(col.name)
        else:
            self._dataset_label.setText("Dataset: none")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "id_column": self._id_combo.currentText(),
            "exclude_numeric": self._exclude_numeric.isChecked(),
            "exclude_zeros": self._exclude_zeros.isChecked(),
            "item_name": self._item_name.text(),
            "value_name": self._value_name.text(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        id_col = str(payload.get("id_column", "(Row number)"))
        if self._id_combo.findText(id_col) >= 0:
            self._id_combo.setCurrentText(id_col)
        self._exclude_numeric.setChecked(bool(payload.get("exclude_numeric", False)))
        self._exclude_zeros.setChecked(bool(payload.get("exclude_zeros", False)))
        self._item_name.setText(str(payload.get("item_name", "item")))
        self._value_name.setText(str(payload.get("value_name", "value")))

    def help_text(self) -> str:
        return "Convert wide-format data to long-format (unpivot). Each value variable becomes a row."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/melt/"

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        id_col = self._id_combo.currentText()
        if id_col == "(Row number)":
            id_col = None

        self._output_dataset = self._service.melt(
            self._dataset_handle,
            id_column=id_col,
            exclude_numeric=self._exclude_numeric.isChecked(),
            exclude_zeros=self._exclude_zeros.isChecked(),
            item_name=self._item_name.text() or "item",
            value_name=self._value_name.text() or "value",
        )

        self._result_label.setText(
            f"Result: {self._output_dataset.row_count} rows x {self._output_dataset.column_count} columns"
        )
        self._notify_output_changed()
