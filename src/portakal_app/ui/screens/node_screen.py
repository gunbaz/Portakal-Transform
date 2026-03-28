from __future__ import annotations

from collections.abc import Callable

from portakal_app.data.models import DatasetHandle
from portakal_app.models import WorkflowPayload


class WorkflowNodeScreenSupport:
    def _init_workflow_node_support(self) -> None:
        self._output_changed_callbacks: list[Callable[[], None]] = []

    def on_output_changed(self, callback: Callable[[], None]) -> None:
        self._output_changed_callbacks.append(callback)

    def _notify_output_changed(self) -> None:
        callbacks = list(getattr(self, "_output_changed_callbacks", ()))
        for callback in callbacks:
            callback()

    def set_input_payload(self, payload: WorkflowPayload | None) -> None:
        _ = payload

    def serialize_node_state(self) -> dict[str, object]:
        return {}

    def restore_node_state(self, payload: dict[str, object]) -> None:
        _ = payload

    def current_output_dataset(self) -> DatasetHandle | None:
        return None

    def current_output_datasets(self) -> dict[str, DatasetHandle | None] | None:
        """Return outputs keyed by port id (e.g. ``{"out-1": ds, "out-2": ds2}``).

        Widgets with a single output port can ignore this method; the runtime
        will fall back to :meth:`current_output_dataset`.  Widgets with
        multiple output ports should override this to provide a dataset per
        port.
        """
        return None
