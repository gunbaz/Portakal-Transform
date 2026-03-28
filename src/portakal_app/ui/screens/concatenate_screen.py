from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
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
from portakal_app.data.services.concatenate_service import ConcatenateService
from portakal_app.ui import i18n
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

        # "Variable Sets Merging" Group
        mode_group = QGroupBox(i18n.t("Variable Sets Merging"))
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setContentsMargins(10, 10, 10, 10)
        mode_layout.setSpacing(6)
        
        mode_layout.addWidget(QLabel(i18n.t("When there is no primary table, the output should contain")))
        self._mode_group = QButtonGroup(self)
        
        self._radio_union = QRadioButton(i18n.t("all variables that appear in input tables"))
        self._radio_intersection = QRadioButton(i18n.t("only variables that appear in all tables"))
        
        self._radio_union.setChecked(True)
        self._mode_group.addButton(self._radio_union, 0)
        self._mode_group.addButton(self._radio_intersection, 1)
        
        mode_layout.addWidget(self._radio_union)
        mode_layout.addWidget(self._radio_intersection)
        
        info_lbl = QLabel(i18n.t("The resulting table will have a class only if there is no conflict\nbetween input classes."))
        info_lbl.setStyleSheet("color: #666;")
        mode_layout.addWidget(info_lbl)
        
        layout.addWidget(mode_group)

        # "Variable matching" Group
        match_group = QGroupBox(i18n.t("Variable matching"))
        match_layout = QVBoxLayout(match_group)
        match_layout.setContentsMargins(10, 10, 10, 10)
        match_layout.setSpacing(6)
        
        self._check_primary_names = QCheckBox(i18n.t("Use column names from the primary table,\nand ignore names in other tables."))
        self._check_same_formula = QCheckBox(i18n.t("Treat variables with the same name as the same variable,\neven if they are computed using different formulae."))
        
        match_layout.addWidget(self._check_primary_names)
        match_layout.addWidget(self._check_same_formula)
        
        layout.addWidget(match_group)

        # "Source Identification" Group
        source_group = QGroupBox(i18n.t("Source Identification"))
        source_layout = QVBoxLayout(source_group)
        source_layout.setContentsMargins(10, 10, 10, 10)
        source_layout.setSpacing(8)
        
        self._add_source = QCheckBox(i18n.t("Append data source IDs"))
        source_layout.addWidget(self._add_source)
        
        name_row = QHBoxLayout()
        name_lbl = QLabel(i18n.t("Feature name:"))
        name_lbl.setFixedWidth(80)
        name_row.addWidget(name_lbl)
        self._source_name = QLineEdit("Source ID")
        name_row.addWidget(self._source_name)
        source_layout.addLayout(name_row)
        
        place_row = QHBoxLayout()
        place_lbl = QLabel(i18n.t("Place:"))
        place_lbl.setFixedWidth(80)
        place_row.addWidget(place_lbl)
        self._source_role = QComboBox()
        self._source_role.addItems([i18n.t("Class attribute"), i18n.t("Meta attribute"), i18n.t("Feature")])
        place_row.addWidget(self._source_role)
        source_layout.addLayout(place_row)
        
        layout.addWidget(source_group)

        self._info_label = QLabel(i18n.t("Primary: -  |  Additional: -"))
        layout.addWidget(self._info_label)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        layout.addStretch(1)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self._apply_button = QPushButton(i18n.t("Apply"))
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
            "use_primary_names_only": self._check_primary_names.isChecked(),
            "add_source": self._add_source.isChecked(),
            "source_name": self._source_name.text(),
            "source_role": self._source_role.currentIndex(),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        mode_id = int(payload.get("merge_mode", 0))
        btn = self._mode_group.button(mode_id)
        if btn:
            btn.setChecked(True)
            
        self._check_primary_names.setChecked(bool(payload.get("use_primary_names_only", False)))
        self._add_source.setChecked(bool(payload.get("add_source", False)))
        self._source_name.setText(str(payload.get("source_name", "Source ID")))
        
        role = str(payload.get("source_role", "Class attribute"))
        if self._source_role.findText(role) >= 0:
            self._source_role.setCurrentText(role)

    def help_text(self) -> str:
        return "Concatenate two or more datasets vertically (append rows)."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/concatenate/"

    def _update_info(self) -> None:
        p = f"{self._primary.row_count}r" if self._primary else "-"
        a = f"{self._additional.row_count}r" if self._additional else "-"
        self._info_label.setText(i18n.tf("Primary: {p}  |  Additional: {a}", p=p, a=a))

    def _apply(self) -> None:
        datasets = [ds for ds in [self._primary, self._additional] if ds is not None]
        if not datasets:
            self._output_dataset = None
            self._result_label.setText("")
            self._notify_output_changed()
            return

        mode = "Intersection" if self._mode_group.checkedId() == 1 else "Union"
        
        role_map = {0: "target", 1: "meta", 2: "feature"}
        mapped_role = role_map.get(self._source_role.currentIndex(), "feature")

        self._output_dataset = self._service.concatenate(
            datasets,
            merge_mode=mode,
            use_primary_names_only=self._check_primary_names.isChecked(),
            add_source_column=self._add_source.isChecked(),
            source_column_name=self._source_name.text() or "Source ID",
            source_column_role=mapped_role,
        )

        if self._output_dataset:
            self._result_label.setText(
                i18n.tf("Result: {rows} rows x {cols} columns", rows=self._output_dataset.row_count, cols=self._output_dataset.column_count)
            )
        else:
            self._result_label.setText(i18n.t("No output."))
        self._notify_output_changed()

    def refresh_translations(self) -> None:
        p = f"{self._primary.row_count}r" if self._primary else "-"
        a = f"{self._additional.row_count}r" if self._additional else "-"
        self._info_label.setText(i18n.tf("Primary: {p}  |  Additional: {a}", p=p, a=a))
        if self._output_dataset is not None:
            self._result_label.setText(
                i18n.tf("Result: {rows} rows x {cols} columns", rows=self._output_dataset.row_count, cols=self._output_dataset.column_count)
            )
