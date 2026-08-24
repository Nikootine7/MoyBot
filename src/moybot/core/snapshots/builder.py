"""Snapshot construction from cached state (PROJECT_SPEC.md §4)."""

from __future__ import annotations

from itertools import count
from typing import final

from moybot.core.model.metrics import TokenMetrics
from moybot.core.model.primitives import Pubkey, Slot, TimestampMs
from moybot.core.model.snapshot import Snapshot
from moybot.core.state.cache_port import ContinuousStateCache

__all__ = ["SnapshotBuilder"]


@final
class SnapshotBuilder:
    """Captures cached token state as an immutable snapshot.

    Sequence numbers are monotonic per builder instance and exist to make the ordering of two
    snapshots unambiguous even when they share a slot and a millisecond.
    """

    def __init__(self, cache: ContinuousStateCache) -> None:
        self._cache = cache
        self._sequence = count()

    def capture(
        self,
        mint: Pubkey,
        slot: Slot | None = None,
        captured_at_ms: TimestampMs | None = None,
    ) -> Snapshot | None:
        """Capture a snapshot, or ``None`` when the token has never been observed.

        Returning ``None`` rather than an empty snapshot keeps "unknown" distinguishable from
        "observed as empty" (PROJECT_SPEC.md §10.8).

        ``slot`` and ``captured_at_ms`` default to the slot and time at which the cached state was
        *observed*, not to the moment the snapshot was built. Staleness then measures the age of
        the information rather than the age of the copy, which is what PROJECT_SPEC.md §5 and
        §10.8 care about.
        """
        cached = self._cache.get(mint)
        if cached is None:
            return None
        return self.capture_state(
            mint,
            cached.metrics,
            slot if slot is not None else cached.last_slot,
            captured_at_ms if captured_at_ms is not None else cached.last_updated_ms,
        )

    def capture_state(
        self,
        mint: Pubkey,
        metrics: TokenMetrics,
        slot: Slot,
        captured_at_ms: TimestampMs,
    ) -> Snapshot:
        """Capture state the caller already holds, without reading or writing the cache.

        Final validation needs a snapshot of a fresh read (PROJECT_SPEC.md §5). That read is not
        an observation, so it must not enter continuous state, where it would become the baseline
        for a later event's decision snapshot and delta (docs/DECISIONS.md D-011).
        """
        return Snapshot(
            mint=mint,
            slot=slot,
            captured_at_ms=captured_at_ms,
            sequence=next(self._sequence),
            metrics=metrics,
        )
