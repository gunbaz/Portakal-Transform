from __future__ import annotations

from PySide6.QtWidgets import (
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
from portakal_app.data.services.select_columns_service import SelectColumnsService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


class SelectColumnsScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = SelectColumnsService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        lists_layout = QHBoxLayout()

        ignored_group = QGroupBox("Ignored")
        ignored_layout = QVBoxLayout(ignored_group)
        ignored_layout.setContentsMargins(6, 6, 6, 6)
        self._ignored_list = QListWidget()
        self._ignored_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        ignored_layout.addWidget(self._ignored_list)
        lists_layout.addWidget(ignored_group)

        features_group = QGroupBox("Features")
        features_layout = QVBoxLayout(features_group)
        features_layout.setContentsMargins(6, 6, 6, 6)
        self._features_list = QListWidget()
        self._features_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        features_layout.addWidget(self._features_list)
        lists_layout.addWidget(features_group)

        target_group = QGroupBox("Target")
        target_layout = QVBoxLayout(target_group)
        target_layout.setContentsMargins(6, 6, 6, 6)
        self._target_list = QListWidget()
        self._target_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        target_layout.addWidget(self._target_list)
        lists_layout.addWidget(target_group)

        meta_group = QGroupBox("Meta")
        meta_layout = QVBoxLayout(meta_group)
        meta_layout.setContentsMargins(6, 6, 6, 6)
        self._meta_list = QListWidget()
        self._meta_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        meta_layout.addWidget(self._meta_list)
        lists_layout.addWidget(meta_group)

        layout.addLayout(lists_layout, 1)

        move_layout = QHBoxLayout()
        self._to_ignored = QPushButton("-> Ignored")
        self._to_ignored.clicked.connect(lambda: self._move_selected("ignored"))
        self._to_features = QPushButton("-> Features")
        self._to_features.clicked.connect(lambda: self._move_selected("features"))
        self._to_target = QPushButton("-> Target")
        self._to_target.clicked.connect(lambda: self._move_selected("target"))
        self._to_meta = QPushButton("-> Meta")
        self._to_meta.clicked.connect(lambda: self._move_selected("meta"))
        self._reset_btn = QPushButton("Reset")
        self._reset_btn.clicked.connect(self._reset_columns)
        move_layout.addWidget(self._to_ignored)
        move_layout.addWidget(self._to_features)
        move_layout.addWidget(self._to_target)
        move_layout.addWidget(self._to_meta)
        move_layout.addStretch(1)
        move_layout.addWidget(self._reset_btn)
        layout.addLayout(move_layout)

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
        self._reset_columns()

    def current_output_dataset(self) -> DatasetHandle | None:
        return self._output_dataset

    def serialize_node_state(self) -> dict[str, object]:
        return {
            "features": _list_items(self._features_list),
            "target": _list_items(self._target_list),
            "metas": _list_items(self._meta_list),
            "ignored": _list_items(self._ignored_list),
        }

    def restore_node_state(self, payload: dict[str, object]) -> None:
        pass

    def help_text(self) -> str:
        return "Assign columns to Features, Target, Meta, or Ignored roles using drag-and-drop style lists."

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/transform/selectcolumns/"

    def _reset_columns(self) -> None:
        self._ignored_list.clear()
        self._features_list.clear()
        self._target_list.clear()
        self._meta_list.clear()

        if self._dataset_handle is None:
            self._dataset_label.setText("Dataset: none")
            return

        self._dataset_label.setText(f"Dataset: {self._dataset_handle.display_name}")
        for col in self._dataset_handle.domain.columns:
            if col.role == "target":
                self._target_list.addItem(QListWidgetItem(col.name))
            elif col.role == "meta":
                self._meta_list.addItem(QListWidgetItem(col.name))
            else:
                self._features_list.addItem(QListWidgetItem(col.name))

    def _move_selected(self, target: str) -> None:
        target_list_map = {
            "ignored": self._ignored_list,
            "features": self._features_list,
            "target": self._target_list,
            "meta": self._meta_list,
        }
        target_list = target_list_map[target]

        for source_list in [self._ignored_list, self._features_list, self._target_list, self._meta_list]:
            if source_list is target_list:
                continue
            selected = source_list.selectedItems()
            for item in selected:
                row = source_list.row(item)
                source_list.takeItem(row)
                target_list.addItem(QListWidgetItem(item.text()))

    def _apply(self) -> None:
        if self._dataset_handle is None:
            self._output_dataset = None
            self._notify_output_changed()
            return

        self._output_dataset = self._service.select(
            self._dataset_handle,
            features=_list_items(self._features_list),
            target=_list_items(self._target_list),
            metas=_list_items(self._meta_list),
        )
        self._notify_output_changed()


def _list_items(list_widget: QListWidget) -> list[str]:
    return [list_widget.item(i).text() for i in range(list_widget.count())]
