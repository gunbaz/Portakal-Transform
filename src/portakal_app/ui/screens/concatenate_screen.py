from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
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
from portakal_app.data.services.concatenate_service import MERGE_MODES, ConcatenateService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class ConcatenateScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = ConcatenateService()
        self._primary: DatasetHandle | None = None
        self._additional: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Primary: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        mode_group = QGroupBox("Domain Merging")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setContentsMargins(10, 10, 10, 10)
        mode_layout.setSpacing(6)
        self._mode_group = QButtonGroup(self)
        for i, mode in enumerate(MERGE_MODES):
            rb = QRadioButton(mode)
            if i == 0:
                rb.setChecked(True)
            self._mode_group.addButton(rb, i)
            mode_layout.addWidget(rb)
        layout.addWidget(mode_group)

        source_group = QGroupBox("Source Column")
        source_layout = QVBoxLayout(source_group)
        source_layout.setContentsMargins(10, 10, 10, 10)
        source_layout.setSpacing(8)
        self._add_source = QCheckBox("Append source column")
        source_layout.addWidget(self._add_source)
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Column name:"))
        self._source_name = QLineEdit("Source")
        name_row.addWidget(self._source_name)
        source_layout.addLayout(name_row)
        layout.addWidget(source_group)

        self._info_label = QLabel("Primary: -  |  Additional: -")
        layout.addWidget(self._info_label)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        layout.addStretch(1)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self._apply_button = QPushButton("Concatenate")
        self._apply_button.setProperty("primary", True)
        self._apply_button.clicked.connect(self._apply)
        footer.addWidget(self._apply_button)
        layout.addLayout(footer)

    def set_input_payload(self, payload) -> None:
        if payload is None:
            self._primary = None
            self._additional = None
        elif payload.port_label == "Primary Data":
            self._primary = payload.dataset
        elif payload.port_label == "Additional Data":
            self._additional = payload.dataset
        self._update_info()

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "merge_mode": self._mode_group.checkedId(),
            "add_source": self._add_source.isChecked(),
            "source_name": self._source_name.text(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        mode_id = int(payload.get("merge_mode", 0))
        btn = self._mode_group.button(mode_id)
        if btn:
            btn.setChecked(True)
        self._add_source.setChecked(bool(payload.get("add_source", False)))
        self._source_name.setText(str(payload.get("source_name", "Source")))

    def help_text(self) -> str:
        return "Concatenate two or more datasets vertically (append rows)."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/concatenate/"

    def _update_info(self) -> None:
        p = f"{self._primary.row_count}r" if self._primary else "-"
        a = f"{self._additional.row_count}r" if self._additional else "-"
        self._info_label.setText(f"Primary: {p}  |  Additional: {a}")
        if self._primary:
            self._dataset_label.setText(f"Primary: {self._primary.display_name}")
        else:
            self._dataset_label.setText("Primary: none")

    def _apply(self) -> None:
        datasets = [ds for ds in [self._primary, self._additional] if ds is not None]
        if not datasets:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        modes = {0: "Union", 1: "Intersection"}
        mode = modes.get(self._mode_group.checkedId(), "Union")

        self._output_dataset = self._service.concatenate(
            datasets,
            merge_mode=mode,
            add_source_column=self._add_source.isChecked(),
            source_column_name=self._source_name.text() or "Source",
        )

        if self._output_dataset:
            self._result_label.setText(
                f"Result: {self._output_dataset.row_count} rows x {self._output_dataset.column_count} columns"
            )
        else:
            self._result_label.setText("No output.")
        self._notify_output_changed()
