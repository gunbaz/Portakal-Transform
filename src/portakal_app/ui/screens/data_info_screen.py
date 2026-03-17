from __future__ import annotations

import csv
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from portakal_app.models import DataInfoViewModel


class DataInfoScreen(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dataset_path: Path | None = None
        self._view_model = DataInfoViewModel()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self._properties_panel = self._build_panel("Data table properties")
        self._properties_label = self._make_body_label("No dataset loaded.")
        self._properties_panel.layout().addWidget(self._properties_label)
        layout.addWidget(self._properties_panel)

        self._attributes_panel = self._build_panel("Additional attributes")
        self._attributes_label = self._make_body_label("No additional metadata available yet.")
        self._attributes_panel.layout().addWidget(self._attributes_label)
        layout.addWidget(self._attributes_panel)

        self._llm_panel = self._build_panel("LLM assistant")
        self._llm_status = self._make_body_label("LLM not connected")
        self._llm_status.setProperty("muted", True)
        self._llm_panel.layout().addWidget(self._llm_status)
        self._llm_body = self._make_body_label(
            "Dataset commentary and suggestions will appear here after the LLM integration is connected."
        )
        self._llm_panel.layout().addWidget(self._llm_body)
        layout.addWidget(self._llm_panel)
        layout.addStretch(1)

        self.set_view_model(None)
        self.set_dataset(None)

    def _build_panel(self, title: str) -> QFrame:
        frame = QFrame(self)
        frame.setProperty("panel", True)
        panel_layout = QVBoxLayout(frame)
        panel_layout.setContentsMargins(14, 12, 14, 12)
        panel_layout.setSpacing(8)
        heading = QLabel(title)
        heading.setProperty("sectionTitle", True)
        heading.setStyleSheet("font-size: 12pt;")
        heading.setAutoFillBackground(False)
        heading.setStyleSheet("font-size: 12pt; background: transparent;")
        panel_layout.addWidget(heading)
        return frame

    def _make_body_label(self, text: str = "") -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setAutoFillBackground(False)
        label.setStyleSheet("background: transparent;")
        return label

    def set_dataset(self, dataset_path: str | None) -> None:
        self._dataset_path = Path(dataset_path) if dataset_path else None
        if self._dataset_path is None or not self._dataset_path.exists():
            self._properties_label.setText("No dataset loaded.")
            self._attributes_label.setText("No additional metadata available yet.")
            return

        suffix = self._dataset_path.suffix.lower()
        if suffix not in {".csv", ".tsv", ".tab"}:
            self._properties_label.setText(
                "\n".join(
                    [
                        f"Name: {self._dataset_path.stem}",
                        "Size: preview not available for this format yet",
                        "Features: pending backend support",
                        "Targets: pending backend support",
                        "Missing data: pending backend support",
                    ]
                )
            )
            self._attributes_label.setText(
                "\n".join(
                    [
                        f"Source: {self._dataset_path}",
                        f"Description: Local dataset loaded from {self._dataset_path.name}.",
                        "Author: -",
                        "Year: -",
                        "Reference: -",
                    ]
                )
            )
            return

        delimiter = "\t" if suffix in {".tsv", ".tab"} else ","
        with self._dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            headers = next(reader, [])
            row_count = 0
            missing_count = 0
            sample_values: list[list[str]] = [[] for _ in headers]
            unique_values: list[set[str]] = [set() for _ in headers]
            for row in reader:
                row_count += 1
                for index in range(len(headers)):
                    value = row[index].strip() if index < len(row) else ""
                    if not value:
                        missing_count += 1
                        continue
                    if len(sample_values[index]) < 1000:
                        sample_values[index].append(value)
                    if len(unique_values[index]) < 24:
                        unique_values[index].add(value)

        type_names = [self._infer_type(values) for values in sample_values]
        numeric_count = sum(1 for value in type_names if value == "numeric")
        target_index = self._infer_target_column(sample_values, unique_values)
        target_text = "none"
        if target_index is not None:
            target_text = f"{type_names[target_index]} outcome with {len(unique_values[target_index])} classes"

        self._properties_label.setText(
            "\n".join(
                [
                    f"Name: {self._dataset_path.stem}",
                    f"Size: ~{row_count} rows, {len(headers)} columns",
                    f"Features: {numeric_count} numeric",
                    f"Targets: {target_text}",
                    f"Missing data: {'none' if missing_count == 0 else missing_count}",
                ]
            )
        )
        self._attributes_label.setText(
            "\n".join(
                [
                    f"Name: {self._dataset_path.stem.replace('_', ' ').title()}",
                    f"Description: Local dataset loaded from {self._dataset_path.name}.",
                    "Author: -",
                    "Year: -",
                    f"Reference: {self._dataset_path}",
                ]
            )
        )

    def set_view_model(self, data_info_view_model: DataInfoViewModel | None) -> None:
        self._view_model = data_info_view_model or DataInfoViewModel()
        self._llm_status.setText(self._view_model.llm_status)
        if self._view_model.suggestions:
            self._llm_body.setText(
                "\n\n".join(f"{item.title}: {item.body}" for item in self._view_model.suggestions)
            )
        else:
            self._llm_body.setText("Dataset commentary and suggestions will appear here after the LLM integration is connected.")

    def help_text(self) -> str:
        return (
            "Inspect dataset properties, additional metadata and future LLM insights. "
            "This screen is intended to mirror Orange's Data Info widget."
        )

    def documentation_url(self) -> str:
        return "https://orangedatamining.com/widget-catalog/data/data-info/"

    def footer_status_text(self) -> str:
        return "Info"

    def _infer_type(self, values: list[str]) -> str:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            return "text"
        if all(self._is_float(value) for value in cleaned):
            return "numeric"
        if all("-" in value or "/" in value or ":" in value for value in cleaned[:8]):
            return "datetime"
        unique_count = len(set(cleaned))
        if unique_count <= max(12, len(cleaned) // 3):
            return "categorical"
        return "text"

    def _infer_target_column(self, sample_values: list[list[str]], unique_values: list[set[str]]) -> int | None:
        candidates: list[tuple[int, int]] = []
        for index, values in enumerate(sample_values):
            if not values:
                continue
            unique_count = len(unique_values[index])
            if unique_count <= 12 and not all(self._is_float(value) for value in values):
                candidates.append((index, unique_count))
        if not candidates:
            return None
        return candidates[-1][0]

    def _is_float(self, value: str) -> bool:
        try:
            float(value)
        except ValueError:
            return False
        return True
