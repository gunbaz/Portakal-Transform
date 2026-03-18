from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable

from portakal_app.data.models import DatasetHandle


ScreenFactory = Callable[[], object]


@dataclass(frozen=True)
class AppState:
    selected_category: str = "data"
    selected_widget: str = "file"
    current_dataset: DatasetHandle | None = None
    current_dataset_id: str | None = None
    current_dataset_path: str | None = None
    workflow_title: str = "Untitled"
    workflow_description: str = ""
    status_message: str = "Ready"

    def with_updates(self, **changes: Any) -> "AppState":
        return replace(self, **changes)


@dataclass(frozen=True)
class CategoryDefinition:
    id: str
    label: str
    enabled: bool = True


@dataclass(frozen=True)
class WidgetDefinition:
    id: str
    category_id: str
    label: str
    enabled: bool
    screen_factory: ScreenFactory
    description: str = ""
    icon_name: str = "file"
    input_ports: tuple["PortDefinition", ...] = ()
    output_ports: tuple["PortDefinition", ...] = ()


@dataclass(frozen=True)
class PortDefinition:
    id: str
    label: str


@dataclass(frozen=True)
class MetricCardData:
    title: str
    value: str
    subtitle: str = ""


@dataclass(frozen=True)
class SuggestionItem:
    title: str
    body: str
    severity: str = "info"


@dataclass(frozen=True)
class DataInfoViewModel:
    summary_cards: list[MetricCardData] = field(default_factory=list)
    column_highlights: list[str] = field(default_factory=list)
    suggestions: list[SuggestionItem] = field(default_factory=list)
    llm_status: str = "LLM not connected"
