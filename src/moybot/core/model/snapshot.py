"""Snapshots (PROJECT_SPEC.md §4).

A snapshot is the immutable record of everything the system knew about one token at one instant.
It carries both a millisecond wall-clock timestamp and a Solana slot so that ordering and
staleness can be reasoned about independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from moybot.core.model.metrics import TokenMetrics
from moybot.core.model.primitives import Pubkey, Slot, TimestampMs

__all__ = ["Snapshot"]


@final
@dataclass(frozen=True, slots=True)
class Snapshot:
    """State of one token at one instant."""

    mint: Pubkey
    slot: Slot
    captured_at_ms: TimestampMs
    sequence: int
    metrics: TokenMetrics

    def age_ms(self, now_ms: TimestampMs) -> int:
        """Wall-clock age of this snapshot in milliseconds."""
        return int(now_ms) - int(self.captured_at_ms)

    def slot_lag(self, current_slot: Slot) -> int:
        """How many slots behind ``current_slot`` this snapshot is."""
        return int(current_slot) - int(self.slot)
