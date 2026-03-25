from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.unique_service import TIEBREAKERS, UniqueService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class UniqueScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = UniqueService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        group_by_group = QGroupBox("Group By")
        group_by_layout = QVBoxLayout(group_by_group)
        group_by_layout.setContentsMargins(10, 10, 10, 10)
        group_by_layout.setSpacing(8)

        self._column_list = QListWidget()
        self._column_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        group_by_layout.addWidget(self._column_list)

        layout.addWidget(group_by_group, 1)

        tiebreaker_group = QGroupBox("Tiebreaker")
        tiebreaker_layout = QVBoxLayout(tiebreaker_group)
        tiebreaker_layout.setContentsMargins(10, 10, 10, 10)
        tiebreaker_layout.setSpacing(8)

        self._tiebreaker_combo = QComboBox()
        self._tiebreaker_combo.addItems(list(TIEBREAKERS))
        self._tiebreaker_combo.setCurrentText("First instance")
        tiebreaker_layout.addWidget(self._tiebreaker_combo)

        layout.addWidget(tiebreaker_group)

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
        self._column_list.clear()

        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
            for col in dataset.domain.columns:
                item = QListWidgetItem(col.name)
                item.setSelected(True)
                self._column_list.addItem(item)
        else:
            self._dataset_label.setText("Dataset: none")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        selected = [self._column_list.item(i).text() for i in range(self._column_list.count()) if self._column_list.item(i).isSelected()]
        return {
            "group_by": selected,
            "tiebreaker": self._tiebreaker_combo.currentText(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        group_by = payload.get("group_by", [])
        if isinstance(group_by, list):
            for i in range(self._column_list.count()):
                item = self._column_list.item(i)
                item.setSelected(item.text() in group_by)
        tiebreaker = payload.get("tiebreaker", "First instance")
        if isinstance(tiebreaker, str):
            self._tiebreaker_combo.setCurrentText(tiebreaker)

    def help_text(self) -> str:
        return "Filter the dataset to keep only unique rows based on selected columns."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/unique/"

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        selected_cols = [
            self._column_list.item(i).text()
            for i in range(self._column_list.count())
            if self._column_list.item(i).isSelected()
        ]

        self._output_dataset = self._service.filter_unique(
            self._dataset_handle,
            group_by_columns=selected_cols,
            tiebreaker=self._tiebreaker_combo.currentText(),
        )

        before = self._dataset_handle.row_count
        after = self._output_dataset.row_count
        self._result_label.setText(f"Rows: {before} -> {after} ({before - after} duplicates removed)")
        self._notify_output_changed()
