from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def _dataset_label(dataset_handle: str | None) -> str:
    if not dataset_handle:
        return "none"
    path = Path(dataset_handle)
    return path.name if path.exists() else dataset_handle


class SaveDataScreen(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dataset_path: Path | None = None
        self.setObjectName("saveDataScreen")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(14)

        self._title = QLabel("Save Data")
        self._title.setProperty("sectionTitle", True)
        self._title.setStyleSheet("background: transparent;")
        layout.addWidget(self._title)

        self._dataset = QLabel("Dataset: none")
        self._dataset.setProperty("muted", True)
        self._dataset.setStyleSheet("background: transparent;")
        layout.addWidget(self._dataset)

        self._annotations_checkbox = QCheckBox("Add type annotations to header")
        self._annotations_checkbox.setStyleSheet("background: transparent;")
        layout.addWidget(self._annotations_checkbox)

        self._autosave_checkbox = QCheckBox("Autosave when receiving new data")
        self._autosave_checkbox.setStyleSheet("background: transparent;")
        layout.addWidget(self._autosave_checkbox)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(12)

        self._save_button = QPushButton("Save")
        self._save_button.setProperty("primary", True)
        self._save_button.setMinimumWidth(150)
        self._save_button.setEnabled(False)
        self._save_button.clicked.connect(self._save_default)
        buttons_row.addWidget(self._save_button)

        self._save_as_button = QPushButton("Save as ...")
        self._save_as_button.setProperty("secondary", True)
        self._save_as_button.setMinimumWidth(150)
        self._save_as_button.setEnabled(False)
        self._save_as_button.clicked.connect(self._save_as)
        buttons_row.addWidget(self._save_as_button)

        layout.addLayout(buttons_row)
        layout.addStretch(1)

    def sizeHint(self) -> QSize:
        return QSize(560, 220)

    def minimumSizeHint(self) -> QSize:
        return QSize(500, 200)

    def set_dataset(self, dataset_handle: str | None) -> None:
        self._dataset_path = Path(dataset_handle) if dataset_handle else None
        self._dataset.setText(f"Dataset: {_dataset_label(dataset_handle)}")
        enabled = self._dataset_path is not None and self._dataset_path.exists()
        self._save_button.setEnabled(enabled)
        self._save_as_button.setEnabled(enabled)

    def help_text(self) -> str:
        return (
            "Save the current dataset to disk. The screen mirrors Orange's Save Data widget "
            "with annotation and autosave options reserved for the backend integration."
        )

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/data/save-data/"

    def footer_status_text(self) -> str:
        if self._dataset_path is None or not self._dataset_path.exists():
            return "0"
        return self._dataset_path.suffix.lower() or "data"

    def _save_default(self) -> None:
        if self._dataset_path is None or not self._dataset_path.exists():
            return
        default_path = self._dataset_path.with_name(f"{self._dataset_path.stem}_copy{self._dataset_path.suffix}")
        self._write_dataset(default_path)

    def _save_as(self) -> None:
        if self._dataset_path is None or not self._dataset_path.exists():
            return
        target_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Data As",
            str(self._dataset_path.with_name(f"{self._dataset_path.stem}_copy{self._dataset_path.suffix}")),
            "Data Files (*.csv *.tsv *.tab *.xlsx *.xls *.parquet);;All Files (*.*)",
        )
        if not target_path:
            return
        self._write_dataset(Path(target_path))

    def _write_dataset(self, target_path: Path) -> None:
        if self._dataset_path is None:
            return
        try:
            if target_path.resolve() == self._dataset_path.resolve():
                QMessageBox.information(self, "Save Data", "Choose a different output path.")
                return
        except OSError:
            pass

        try:
            shutil.copyfile(self._dataset_path, target_path)
        except OSError as exc:
            QMessageBox.warning(self, "Save Data", f"Could not save dataset.\n\n{exc}")
            return

        QMessageBox.information(self, "Save Data", f"Dataset saved to:\n{target_path}")
