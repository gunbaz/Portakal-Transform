from __future__ import annotations

from portakal_app.models import CategoryDefinition, PortDefinition, WidgetDefinition
from portakal_app.ui import i18n
from portakal_app.ui.screens.color_screen import ColorScreen
from portakal_app.ui.screens.column_statistics_screen import ColumnStatisticsScreen
from portakal_app.ui.screens.csv_import_screen import CSVImportScreen
from portakal_app.ui.screens.data_info_screen import DataInfoScreen
from portakal_app.ui.screens.data_table_screen import DataTableScreen
from portakal_app.ui.screens.datasets_screen import DatasetsScreen
from portakal_app.ui.screens.edit_domain_screen import EditDomainScreen
from portakal_app.ui.screens.file_screen import FileScreen
from portakal_app.ui.screens.paint_data_screen import PaintDataScreen
from portakal_app.ui.screens.placeholder_screen import PlaceholderScreen
from portakal_app.ui.screens.rank_screen import RankScreen
from portakal_app.ui.screens.save_data_screen import SaveDataScreen


def _placeholder_factory(title: str, description: str):
    def factory() -> PlaceholderScreen:
        return PlaceholderScreen(title=i18n.t(title), message=i18n.t(description))

    return factory


def _inputs(*labels: str) -> tuple[PortDefinition, ...]:
    return tuple(PortDefinition(id=f"in-{index}", label=label) for index, label in enumerate(labels, start=1))


def _outputs(*labels: str) -> tuple[PortDefinition, ...]:
    return tuple(PortDefinition(id=f"out-{index}", label=label) for index, label in enumerate(labels, start=1))


def build_categories() -> list[CategoryDefinition]:
    return [
        CategoryDefinition(id="data", label=i18n.t("Data")),
        CategoryDefinition(id="transform", label=i18n.t("Transform")),
        CategoryDefinition(id="visualize", label=i18n.t("Visualize")),
        CategoryDefinition(id="model", label=i18n.t("Model")),
        CategoryDefinition(id="evaluate", label=i18n.t("Evaluate")),
        CategoryDefinition(id="unsupervised", label=i18n.t("Unsupervised")),
    ]


def build_widgets() -> list[WidgetDefinition]:
    return [
        WidgetDefinition(
            "file",
            "data",
            i18n.t("File"),
            True,
            FileScreen,
            i18n.t("Load a file dataset."),
            "file",
            (),
            _outputs("Data"),
        ),
        WidgetDefinition(
            "csv-import",
            "data",
            i18n.t("CSV File Import"),
            True,
            CSVImportScreen,
            i18n.t("Preset-based import flow."),
            "csv",
            (),
            _outputs("Data"),
        ),
        WidgetDefinition(
            "datasets",
            "data",
            i18n.t("Datasets"),
            True,
            DatasetsScreen,
            i18n.t("Explore packaged datasets."),
            "dataset",
            (),
            _outputs("Data"),
        ),
        WidgetDefinition(
            "data-table",
            "data",
            i18n.t("Data Table"),
            True,
            DataTableScreen,
            i18n.t("Inspect loaded rows."),
            "table",
            _inputs("Data"),
            _outputs("Data"),
        ),
        WidgetDefinition(
            "paint-data",
            "data",
            i18n.t("Paint Data"),
            True,
            PaintDataScreen,
            i18n.t("Edit data manually."),
            "paint",
            _inputs("Data"),
            _outputs("Data"),
        ),
        WidgetDefinition(
            "data-info",
            "data",
            i18n.t("Data Info"),
            True,
            DataInfoScreen,
            i18n.t("Profile the dataset."),
            "info",
            _inputs("Data"),
            (),
        ),
        WidgetDefinition(
            "rank",
            "data",
            i18n.t("Rank"),
            True,
            RankScreen,
            i18n.t("Rank features."),
            "rank",
            _inputs("Data"),
            _outputs("Scores"),
        ),
        WidgetDefinition(
            "edit-domain",
            "data",
            i18n.t("Edit Domain"),
            True,
            EditDomainScreen,
            i18n.t("Manage column roles."),
            "edit",
            _inputs("Data"),
            _outputs("Data"),
        ),
        WidgetDefinition(
            "color",
            "data",
            i18n.t("Color"),
            True,
            ColorScreen,
            i18n.t("Assign color metadata."),
            "color",
            _inputs("Data"),
            _outputs("Data"),
        ),
        WidgetDefinition(
            "column-statistics",
            "data",
            i18n.t("Column Statistics"),
            True,
            ColumnStatisticsScreen,
            i18n.t("Deep dive into column distributions."),
            "stats",
            _inputs("Data"),
            (),
        ),
        WidgetDefinition(
            "save-data",
            "data",
            i18n.t("Save Data"),
            True,
            SaveDataScreen,
            i18n.t("Export the current dataset."),
            "save",
            _inputs("Data"),
            (),
        ),
        WidgetDefinition(
            "select-columns",
            "transform",
            i18n.t("Select Columns"),
            False,
            _placeholder_factory("Select Columns", "Transform widgets are planned but not part of this shell milestone."),
            i18n.t("Choose feature sets."),
            "columns",
            _inputs("Data"),
            _outputs("Data"),
        ),
        WidgetDefinition(
            "normalize",
            "transform",
            i18n.t("Normalize"),
            False,
            _placeholder_factory("Normalize", "Transform widgets are planned but not part of this shell milestone."),
            i18n.t("Scale numeric columns."),
            "normalize",
            _inputs("Data"),
            _outputs("Data"),
        ),
        WidgetDefinition(
            "scatter-plot",
            "visualize",
            i18n.t("Scatter Plot"),
            False,
            _placeholder_factory("Scatter Plot", "Visualization widgets will be integrated by a later group."),
            i18n.t("Explore points visually."),
            "scatter",
            _inputs("Data"),
            (),
        ),
        WidgetDefinition(
            "linear-regression",
            "model",
            i18n.t("Linear Regression"),
            False,
            _placeholder_factory("Linear Regression", "Model widgets will be integrated by a later group."),
            i18n.t("Train a baseline model."),
            "model",
            _inputs("Data"),
            _outputs("Model"),
        ),
        WidgetDefinition(
            "test-score",
            "evaluate",
            i18n.t("Test & Score"),
            False,
            _placeholder_factory("Test & Score", "Evaluation widgets will be integrated by a later group."),
            i18n.t("Measure model performance."),
            "score",
            _inputs("Data", "Model"),
            _outputs("Scores"),
        ),
        WidgetDefinition(
            "pca",
            "unsupervised",
            i18n.t("PCA"),
            False,
            _placeholder_factory("PCA", "Unsupervised widgets will be integrated by a later group."),
            i18n.t("Reduce dimensionality."),
            "pca",
            _inputs("Data"),
            _outputs("Data"),
        ),
    ]
