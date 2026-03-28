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
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QRectF

from portakal_app.data.models import DatasetHandle
from portakal_app.data.services.select_columns_service import SelectColumnsService
from portakal_app.ui.screens.node_screen import WorkflowNodeScreenSupport


def _create_type_icon(logical_type: str) -> QIcon:
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    if logical_type == "numeric":
        color = QColor("#ef4444")
        text = "N"
    elif logical_type in ("categorical", "boolean"):
        color = QColor("#22c55e")
        text = "C"
    elif logical_type in ("text", "string"):
        color = QColor("#8b5cf6")
        text = "S"
    elif logical_type in ("datetime", "date", "time"):
        color = QColor("#3b82f6")
        text = "D"
    else:
        color = QColor("#6b7280")
        text = "?"

    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, 16, 16, 3, 3)
    
    painter.setPen(QColor("white"))
    font = QFont("Arial", 9, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(QRectF(0, 0, 16, 16), Qt.AlignmentFlag.AlignCenter, text)
    painter.end()
    
    return QIcon(pixmap)


class SelectColumnsScreen(QWidget, WorkflowNodeScreenSupport):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_workflow_node_support()
        self._service = SelectColumnsService()
        self._dataset_handle: DatasetHandle | None = None
        self._output_dataset: DatasetHandle | None = None
        self._saved_roles: dict[str, str] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self._dataset_label = QLabel("Dataset: none")
        self._dataset_label.setProperty("sectionTitle", True)
        self._dataset_label.setStyleSheet("font-size: 12pt; background: transparent;")
        layout.addWidget(self._dataset_label)

        main_boxes_layout = QHBoxLayout()

        # LEFT PANE: Ignored
        ignored_group = QGroupBox("Ignored")
        ignored_layout = QVBoxLayout(ignored_group)
        ignored_layout.setContentsMargins(6, 6, 6, 6)
        self._ignored_list = QListWidget()
        self._ignored_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        ignored_layout.addWidget(self._ignored_list)
        main_boxes_layout.addWidget(ignored_group, 1)

        # MIDDLE PANE: Buttons
        btn_layout = QVBoxLayout()
        btn_layout.addStretch(1)
        
        self._to_features = QPushButton("Features >")
        self._to_features.clicked.connect(lambda: self._move_selected("features"))
        btn_layout.addWidget(self._to_features)
        
        self._to_target = QPushButton("Target >")
        self._to_target.clicked.connect(lambda: self._move_selected("target"))
        btn_layout.addWidget(self._to_target)
        
        self._to_meta = QPushButton("Meta >")
        self._to_meta.clicked.connect(lambda: self._move_selected("meta"))
        btn_layout.addWidget(self._to_meta)
        
        btn_layout.addSpacing(20)
        
        self._to_ignored = QPushButton("< Ignored")
        self._to_ignored.clicked.connect(lambda: self._move_selected("ignored"))
        btn_layout.addWidget(self._to_ignored)
        
        btn_layout.addStretch(1)
        main_boxes_layout.addLayout(btn_layout)

        # RIGHT PANE: Features, Target, Meta
        right_panel = QVBoxLayout()
        
        features_group = QGroupBox("Features")
        features_layout = QVBoxLayout(features_group)
        features_layout.setContentsMargins(6, 6, 6, 6)
        self._features_list = QListWidget()
        self._features_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        features_layout.addWidget(self._features_list)
        right_panel.addWidget(features_group, 3)
        
        target_group = QGroupBox("Target")
        target_layout = QVBoxLayout(target_group)
        target_layout.setContentsMargins(6, 6, 6, 6)
        self._target_list = QListWidget()
        self._target_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        target_layout.addWidget(self._target_list)
        right_panel.addWidget(target_group, 1)
        
        meta_group = QGroupBox("Meta")
        meta_layout = QVBoxLayout(meta_group)
        meta_layout.setContentsMargins(6, 6, 6, 6)
        self._meta_list = QListWidget()
        self._meta_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        meta_layout.addWidget(self._meta_list)
        right_panel.addWidget(meta_group, 1)

        main_boxes_layout.addLayout(right_panel, 1)
        layout.addLayout(main_boxes_layout, 1)

        # Bottom Bar
        bottom_layout = QHBoxLayout()
        self._reset_btn = QPushButton("Reset")
        self._reset_btn.clicked.connect(self._reset_columns)
        bottom_layout.addWidget(self._reset_btn)
        
        bottom_layout.addStretch(1)
        self._apply_button = QPushButton("Apply")
        self._apply_button.setProperty("primary", True)
        self._apply_button.clicked.connect(self._apply)
        bottom_layout.addWidget(self._apply_button)
        
        layout.addLayout(bottom_layout)

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
        self._saved_roles = {}
        for col_name in payload.get("features", []):
            self._saved_roles[col_name] = "feature"
        for col_name in payload.get("target", []):
            self._saved_roles[col_name] = "target"
        for col_name in payload.get("metas", []):
            self._saved_roles[col_name] = "meta"
        for col_name in payload.get("ignored", []):
            self._saved_roles[col_name] = "ignored"
            
        if self._dataset_handle:
            self._reset_columns()

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
            item = QListWidgetItem(col.name)
            item.setIcon(_create_type_icon(col.logical_type))
            item.setData(Qt.ItemDataRole.UserRole, col.logical_type)
            
            role = self._saved_roles.get(col.name, col.role)
            if role == "target":
                self._target_list.addItem(item)
            elif role == "meta" or role == "metas":
                self._meta_list.addItem(item)
            elif role == "ignored":
                self._ignored_list.addItem(item)
            else:
                self._features_list.addItem(item)

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
                taken_item = source_list.takeItem(row)
                target_list.addItem(taken_item)

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
