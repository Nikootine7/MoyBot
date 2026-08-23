"""Decision provenance (PROJECT_SPEC.md §4).

Every stage outcome after an event — including rejections and cancellations — is recorded, so
that it is always possible to reconstruct exactly what information the bot had when it acted.

Provenance records deliberately carry stage timings. PROJECT_SPEC.md §9 leaves the latency
target open, so Phase 1 measures without asserting anything about the measurements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import final

from moybot.core.model.primitives import JsonValue, Pubkey, Slot, TimestampMs
from moybot.core.pipeline.stage import StageName

__all__ = ["ProvenanceRecord"]


@final
@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    """One auditable stage outcome."""

    record_id: str
    correlation_id: str
    stage: StageName
    mint: Pubkey
    occurred_at_ms: TimestampMs
    slot: Slot | None
    outcome: str
    duration_us: int | None = None
    detail: dict[str, JsonValue] = field(default_factory=dict)
