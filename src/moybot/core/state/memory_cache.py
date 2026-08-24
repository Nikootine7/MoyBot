"""In-memory continuous state cache.

Phase 1 keeps warm state in process (docs/DECISIONS.md D-005). The cache technology remains an
open question; only this implementation would change.
"""

from __future__ import annotations

from typing import final

from moybot.core.model.metrics import TokenMetrics, WalletHistory
from moybot.core.model.primitives import Pubkey
from moybot.core.state.cache_port import CachedToken, MetricsPatch
from moybot.core.state.merge import merge_metrics

__all__ = ["InMemoryStateCache"]


@final
class InMemoryStateCache:
    """Latest observed state per token and per wallet, held in process."""

    def __init__(self) -> None:
        self._tokens: dict[Pubkey, CachedToken] = {}
        self._wallets: dict[Pubkey, WalletHistory] = {}

    def apply(self, patch: MetricsPatch) -> CachedToken:
        """Merge only the fields the source reported, leaving all others untouched."""
        current = self._tokens.get(patch.mint)
        base = current.metrics if current is not None else TokenMetrics()
        updated = CachedToken(
            mint=patch.mint,
            metrics=merge_metrics(base, patch.fields),
            last_slot=patch.slot,
            last_updated_ms=patch.observed_at_ms,
        )
        self._tokens[patch.mint] = updated
        return updated

    def get(self, mint: Pubkey) -> CachedToken | None:
        return self._tokens.get(mint)

    def record_wallet_history(self, history: WalletHistory) -> None:
        self._wallets[history.wallet] = history

    def wallet_history(self, wallet: Pubkey) -> WalletHistory | None:
        return self._wallets.get(wallet)

    def tracked_mints(self) -> tuple[Pubkey, ...]:
        return tuple(self._tokens)
