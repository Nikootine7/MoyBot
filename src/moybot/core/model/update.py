"""Ingestion type for continuous data (PROJECT_SPEC.md §2.1, §2.2).

A ``MarketUpdate`` is what a data source hands to the pipeline: a partial observation of one
token plus any events the source explicitly declares. Detectors never invent events from the
metrics (docs/DECISIONS.md D-004, and PROJECT_SPEC.md §2.2 where the event list is examples).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from moybot.core.model.event import Event
from moybot.core.model.primitives import Pubkey, Slot, TimestampMs
from moybot.core.state.cache_port import MetricsPatch

__all__ = ["MarketUpdate"]


@final
@dataclass(frozen=True, slots=True)
class MarketUpdate:
    """One observation of one token, as delivered by a data source."""

    mint: Pubkey
    slot: Slot
    observed_at_ms: TimestampMs
    source: str
    sequence: int
    metrics: tuple[tuple[str, object], ...] = ()
    declared_events: tuple[Event, ...] = ()

    def to_patch(self) -> MetricsPatch:
        """Convert the reported metric fields into a cache patch."""
        return MetricsPatch(
            mint=self.mint,
            slot=self.slot,
            observed_at_ms=self.observed_at_ms,
            fields=self.metrics,
        )
