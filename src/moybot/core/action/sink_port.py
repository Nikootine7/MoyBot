"""Action sink port (PROJECT_SPEC.md §2 "ACTION")."""

from __future__ import annotations

from typing import Protocol

from moybot.core.model.alert import Alert

__all__ = ["ActionSink"]


class ActionSink(Protocol):
    """Terminal stage of the pipeline.

    In Phase 1 the only permitted action is raising an alert (docs/DECISIONS.md D-003).
    """

    @property
    def name(self) -> str:
        """Stable identifier recorded in provenance."""

    def emit(self, alert: Alert) -> None:
        """Deliver an alert."""
