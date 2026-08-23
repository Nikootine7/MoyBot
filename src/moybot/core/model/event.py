"""Event triggers (PROJECT_SPEC.md §2.2).

PROJECT_SPEC.md lists event types as *examples*, so ``EventKind`` is deliberately an open
string rather than an enumeration: Phase 1 does not decide which events exist. Detectors only
surface events that a data source explicitly declares (docs/DECISIONS.md D-004).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NewType, final

from moybot.core.model.primitives import Pubkey, Slot, TimestampMs

__all__ = ["Event", "EventKind", "parse_event_kind"]

EventKind = NewType("EventKind", str)
"""Source-declared event label. Not an enumeration; see module docstring."""


def parse_event_kind(raw: str) -> EventKind:
    """Validate and wrap a source-declared event label."""
    label = raw.strip()
    if not label:
        msg = "event kind must be a non-empty label"
        raise ValueError(msg)
    return EventKind(label)


@final
@dataclass(frozen=True, slots=True)
class Event:
    """A market event that pushes one token into the analysis pipeline."""

    kind: EventKind
    mint: Pubkey
    slot: Slot
    timestamp_ms: TimestampMs
    source: str
    payload: tuple[tuple[str, str], ...] = field(default=())
