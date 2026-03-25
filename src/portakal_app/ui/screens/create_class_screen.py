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
from portakal_app.data.services.create_class_service import CreateClassService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class _RuleRow(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Class label")
        layout.addWidget(self.label_edit, 1)

        self.pattern_edit = QLineEdit()
        self.pattern_edit.setPlaceholderText("Pattern / substring")
        layout.addWidget(self.pattern_edit, 1)

        self.remove_btn = QPushButton("x")
        self.remove_btn.setFixedWidth(30)
        layout.addWidget(self.remove_btn)

    def get_rule(self) -> tuple[str, str]:
        return (self.label_edit.text(), self.pattern_edit.text())


class CreateClassScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = CreateClassService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None
        self._rule_rows: list[_RuleRow] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        source_group = QGroupBox("Source")
        source_layout = QVBoxLayout(source_group)
        source_layout.setContentsMargins(10, 10, 10, 10)
        source_layout.setSpacing(8)

        src_row = QHBoxLayout()
        src_row.addWidget(QLabel("Column:"))
        self._source_combo = QComboBox()
        src_row.addWidget(self._source_combo, 1)
        source_layout.addLayout(src_row)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Class name:"))
        self._class_name = QLineEdit("class")
        name_row.addWidget(self._class_name, 1)
        source_layout.addLayout(name_row)

        opts_row = QHBoxLayout()
        self._case_sensitive = QCheckBox("Case sensitive")
        self._use_regex = QCheckBox("Regular expressions")
        self._match_beginning = QCheckBox("Match beginning")
        opts_row.addWidget(self._case_sensitive)
        opts_row.addWidget(self._use_regex)
        opts_row.addWidget(self._match_beginning)
        source_layout.addLayout(opts_row)

        layout.addWidget(source_group)

        rules_group = QGroupBox("Rules (label -> pattern)")
        self._rules_layout = QVBoxLayout(rules_group)
        self._rules_layout.setContentsMargins(10, 10, 10, 10)
        self._rules_layout.setSpacing(6)
        layout.addWidget(rules_group, 1)

        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("+ Add Rule")
        self._add_btn.clicked.connect(self._add_rule)
        btn_row.addWidget(self._add_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

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
        self._source_combo.clear()

        if dataset:
            self._dataset_label.setText(f"Dataset: {dataset.display_name}")
            for col in dataset.domain.columns:
                if col.logical_type in ("text", "categorical"):
                    self._source_combo.addItem(col.name)
        else:
            self._dataset_label.setText("Dataset: none")
            self._result_label.setText("")

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        rules = [row.get_rule() for row in self._rule_rows]
        return {
            "source": self._source_combo.currentText(),
            "class_name": self._class_name.text(),
            "case_sensitive": self._case_sensitive.isChecked(),
            "use_regex": self._use_regex.isChecked(),
            "match_beginning": self._match_beginning.isChecked(),
            "rules": rules,
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        pass

    def help_text(self) -> str:
        return "Create a new class column based on pattern matching rules applied to a string column."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/createclass/"

    def _add_rule(self) -> None:
        row = _RuleRow(self)
        row.remove_btn.clicked.connect(lambda: self._remove_rule(row))
        self._rule_rows.append(row)
        self._rules_layout.addWidget(row)

    def _remove_rule(self, row: _RuleRow) -> None:
        if row in self._rule_rows:
            self._rule_rows.remove(row)
            self._rules_layout.removeWidget(row)
            row.deleteLater()

    def _apply(self) -> None:
        if self._dataset_handle is None or not self._source_combo.currentText():
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        rules = [row.get_rule() for row in self._rule_rows if row.pattern_edit.text()]

        self._output_dataset = self._service.create_class(
            self._dataset_handle,
            source_column=self._source_combo.currentText(),
            rules=rules,
            class_name=self._class_name.text() or "class",
            case_sensitive=self._case_sensitive.isChecked(),
            use_regex=self._use_regex.isChecked(),
            match_beginning=self._match_beginning.isChecked(),
        )

        unique_classes = self._output_dataset.dataframe.get_column(
            self._class_name.text() or "class"
        ).n_unique()
        self._result_label.setText(f"Created '{self._class_name.text()}' with {unique_classes} classes")
        self._notify_output_changed()
