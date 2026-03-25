from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.group_by_service import AGGREGATIONS, GroupByService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class GroupByScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = GroupByService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        group_group = QGroupBox("Group By Columns")
        group_layout = QVBoxLayout(group_group)
        group_layout.setContentsMargins(10, 10, 10, 10)
        self._group_list = QListWidget()
        self._group_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        group_layout.addWidget(self._group_list)
        layout.addWidget(group_group)

        agg_group = QGroupBox("Aggregations")
        agg_layout = QVBoxLayout(agg_group)
        agg_layout.setContentsMargins(10, 10, 10, 10)
        agg_layout.setSpacing(4)
        self._agg_checks: dict[str, QCheckBox] = {}
        for agg in AGGREGATIONS:
            cb = QCheckBox(agg)
            if agg == "Mean":
                cb.setChecked(True)
            self._agg_checks[agg] = cb
            agg_layout.addWidget(cb)
        layout.addWidget(agg_group)

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
        self._group_list.clear()

        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
            for col in dataset.domain.columns:
                self._group_list.addItem(QListWidgetItem(col.name))
        else:
            self._dataset_label.setText("Dataset: none")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        group_cols = [
            self._group_list.item(i).text()
            for i in range(self._group_list.count())
            if self._group_list.item(i).isSelected()
        ]
        aggs = [name for name, cb in self._agg_checks.items() if cb.isChecked()]
        return {"group_columns": group_cols, "aggregations": aggs}

    def restore_node_state(self, payload: dict[str, object]) -> None:
        group_cols = payload.get("group_columns", [])
        if isinstance(group_cols, list):
            for i in range(self._group_list.count()):
                item = self._group_list.item(i)
                item.setSelected(item.text() in group_cols)
        aggs = payload.get("aggregations", ["Mean"])
        if isinstance(aggs, list):
            for name, cb in self._agg_checks.items():
                cb.setChecked(name in aggs)

    def help_text(self) -> str:
        return "Group the dataset by selected columns and compute aggregations (mean, sum, count, etc.)."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/groupby/"

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        group_cols = [
            self._group_list.item(i).text()
            for i in range(self._group_list.count())
            if self._group_list.item(i).isSelected()
        ]
        selected_aggs = [name for name, cb in self._agg_checks.items() if cb.isChecked()]

        value_cols = [c.name for c in self._dataset_handle.domain.columns if c.name not in group_cols]
        aggregations = {col: selected_aggs for col in value_cols}

        self._output_dataset = self._service.group_by(
            self._dataset_handle,
            group_columns=group_cols,
            aggregations=aggregations,
        )

        self._result_label.setText(
            f"Groups: {self._output_dataset.row_count} | Columns: {self._output_dataset.column_count}"
        )
        self._notify_output_changed()
