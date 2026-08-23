"""Event detector port (PROJECT_SPEC.md §2.2)."""

from __future__ import annotations

from typing import Protocol

from moybot.core.model.event import Event
from moybot.core.model.update import MarketUpdate

__all__ = ["EventDetector"]


class EventDetector(Protocol):
    """Turns an observation into zero or more events.

    Phase 1 ships no heuristic detector. PROJECT_SPEC.md §2.2 gives event types as examples, so
    inventing a spike rule here would convert an example into a requirement.
    """

    @property
    def name(self) -> str:
        """Stable identifier used in logs and provenance."""

    def detect(self, update: MarketUpdate) -> tuple[Event, ...]:
        """Return the events this detector recognises in the update."""
