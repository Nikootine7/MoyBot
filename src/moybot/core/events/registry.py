"""Event detector registry (PROJECT_SPEC.md §2.2)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import final

from moybot.core.events.detector_port import EventDetector
from moybot.core.model.event import Event
from moybot.core.model.update import MarketUpdate

__all__ = ["DeclaredEventDetector", "EventDetectorRegistry"]


@final
class DeclaredEventDetector:
    """Surfaces exactly the events a data source declared, and nothing else.

    This is the only detector in Phase 1 (docs/DECISIONS.md D-004). It derives nothing from the
    metrics, so no detection threshold is implied.
    """

    @property
    def name(self) -> str:
        return "declared_events"

    def detect(self, update: MarketUpdate) -> tuple[Event, ...]:
        return update.declared_events


@final
class EventDetectorRegistry:
    """Runs the registered detectors in order and concatenates their events."""

    def __init__(self, detectors: Sequence[EventDetector]) -> None:
        self._detectors = tuple(detectors)

    @property
    def detector_names(self) -> tuple[str, ...]:
        return tuple(detector.name for detector in self._detectors)

    def detect(self, update: MarketUpdate) -> tuple[Event, ...]:
        events: list[Event] = []
        for detector in self._detectors:
            events.extend(detector.detect(update))
        return tuple(events)
