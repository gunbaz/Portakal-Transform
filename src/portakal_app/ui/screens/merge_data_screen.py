from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.merge_data_service import JOIN_TYPES, MergeDataService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class MergeDataScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = MergeDataService()
        self._dataset_handle: DatasetHandle | None = None
        self._extra_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Data: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        match_group = QGroupBox("Match Columns")
        match_layout = QVBoxLayout(match_group)
        match_layout.setContentsMargins(10, 10, 10, 10)
        match_layout.setSpacing(8)

        left_row = QHBoxLayout()
        left_row.addWidget(QLabel("Data column:"))
        self._left_combo = QComboBox()
        left_row.addWidget(self._left_combo, 1)
        match_layout.addLayout(left_row)

        right_row = QHBoxLayout()
        right_row.addWidget(QLabel("Extra column:"))
        self._right_combo = QComboBox()
        right_row.addWidget(self._right_combo, 1)
        match_layout.addLayout(right_row)
        layout.addWidget(match_group)

        join_group = QGroupBox("Join Type")
        join_layout = QVBoxLayout(join_group)
        join_layout.setContentsMargins(10, 10, 10, 10)
        join_layout.setSpacing(6)
        self._join_group = QButtonGroup(self)
        for i, jt in enumerate(JOIN_TYPES):
            rb = QRadioButton(jt)
            if i == 0:
                rb.setChecked(True)
            self._join_group.addButton(rb, i)
            join_layout.addWidget(rb)
        layout.addWidget(join_group)

        self._data_info = QLabel("Data: -  |  Extra: -")
        layout.addWidget(self._data_info)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        layout.addStretch(1)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self._apply_button = QPushButton("Merge")
        self._apply_button.setProperty("primary", True)
        self._apply_button.clicked.connect(self._apply)
        footer.addWidget(self._apply_button)
        layout.addLayout(footer)

    def set_input_payload(self, payload) -> None:
        if payload is None:
            self._dataset_handle = None
            self._extra_handle = None
        elif payload.port_label == "Data":
            self._dataset_handle = payload.dataset
        elif payload.port_label == "Extra Data":
            self._extra_handle = payload.dataset
        self._update_combos()

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "left_on": self._left_combo.currentText(),
            "right_on": self._right_combo.currentText(),
            "join_type": self._join_group.checkedId(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        lo = str(payload.get("left_on", ""))
        if lo and self._left_combo.findText(lo) >= 0:
            self._left_combo.setCurrentText(lo)
        ro = str(payload.get("right_on", ""))
        if ro and self._right_combo.findText(ro) >= 0:
            self._right_combo.setCurrentText(ro)
        jt = int(payload.get("join_type", 0))
        btn = self._join_group.button(jt)
        if btn:
            btn.setChecked(True)

    def help_text(self) -> str:
        return "Merge two datasets by matching column values (left, inner, or outer join)."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/mergedata/"

    def _update_combos(self) -> None:
        self._left_combo.clear()
        self._right_combo.clear()

        if self._dataset_handle:
            self._dataset_label.setText(f"Data: {self._dataset_handle.display_name}")
            for col in self._dataset_handle.domain.columns:
                self._left_combo.addItem(col.name)
        else:
            self._dataset_label.setText("Data: none")

        if self._extra_handle:
            for col in self._extra_handle.domain.columns:
                self._right_combo.addItem(col.name)

        d_info = f"{self._dataset_handle.row_count}r" if self._dataset_handle else "-"
        e_info = f"{self._extra_handle.row_count}r" if self._extra_handle else "-"
        self._data_info.setText(f"Data: {d_info}  |  Extra: {e_info}")

    def _apply(self) -> None:
        if self._dataset_handle is None or self._extra_handle is None:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        join_types = {0: "Left Join", 1: "Inner Join", 2: "Outer Join"}
        jt = join_types.get(self._join_group.checkedId(), "Left Join")

        self._output_dataset = self._service.merge(
            self._dataset_handle,
            self._extra_handle,
            left_on=self._left_combo.currentText(),
            right_on=self._right_combo.currentText(),
            join_type=jt,
        )

        self._result_label.setText(
            f"Result: {self._output_dataset.row_count} rows x {self._output_dataset.column_count} columns"
        )
        self._notify_output_changed()
