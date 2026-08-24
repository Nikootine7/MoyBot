"""Port for the continuous state cache (PROJECT_SPEC.md §2.1).

The cache exists so that a signal does not force the system to recompute a token's state from
zero (§2.1, §10.3). It is a port so that the storage technology stays an open question
(PROJECT_SPEC.md §9) instead of leaking into the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, final

from moybot.core.model.metrics import MetricFields, TokenMetrics, WalletHistory
from moybot.core.model.primitives import Pubkey, Slot, TimestampMs

__all__ = ["CachedToken", "ContinuousStateCache", "MetricsPatch"]


@final
@dataclass(frozen=True, slots=True)
class CachedToken:
    """Latest known state for one token, with the point in time it was observed at."""

    mint: Pubkey
    metrics: TokenMetrics
    last_slot: Slot
    last_updated_ms: TimestampMs


@final
@dataclass(frozen=True, slots=True)
class MetricsPatch:
    """A partial update to a token's cached metrics.

    ``fields`` contains only the metric fields the data source actually reported. Fields absent
    from a patch are left untouched, so "not reported now" is never confused with "known to be
    zero".
    """

    mint: Pubkey
    slot: Slot
    observed_at_ms: TimestampMs
    fields: MetricFields


class ContinuousStateCache(Protocol):
    """Warm state for the token universe."""

    def apply(self, patch: MetricsPatch) -> CachedToken:
        """Merge a partial observation and return the resulting cached state."""

    def get(self, mint: Pubkey) -> CachedToken | None:
        """Return cached state for one token, or ``None`` when it was never observed."""

    def record_wallet_history(self, history: WalletHistory) -> None:
        """Store observed wallet history (PROJECT_SPEC.md §2.1)."""

    def wallet_history(self, wallet: Pubkey) -> WalletHistory | None:
        """Return observed history for one wallet, or ``None``."""

    def tracked_mints(self) -> tuple[Pubkey, ...]:
        """All mints currently held in the cache."""
