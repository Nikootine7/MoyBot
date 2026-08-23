"""In-memory continuous state cache.

Phase 1 keeps warm state in process (docs/DECISIONS.md D-005). The cache technology remains an
open question; only this implementation would change.

A patch is merged field by field rather than reflectively, so that a reported value whose type
does not match the domain model is rejected instead of being written into the cache.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields
from decimal import Decimal
from typing import final

from moybot.core.model.metrics import (
    HolderDistribution,
    LpState,
    MetricFields,
    MetricValue,
    TokenMetrics,
    TokenState,
    WalletHistory,
)
from moybot.core.model.primitives import Pubkey
from moybot.core.state.cache_port import CachedToken, MetricsPatch

__all__ = ["InMemoryStateCache"]

_METRIC_FIELDS: frozenset[str] = frozenset(field.name for field in fields(TokenMetrics))

type _Values = Mapping[str, MetricValue]


def _type_error(name: str, value: MetricValue, expected: str) -> TypeError:
    return TypeError(f"metric field {name!r} expects {expected}, got {type(value).__name__}")


def _decimal(values: _Values, name: str, current: Decimal | None) -> Decimal | None:
    if name not in values:
        return current
    value = values[name]
    if value is None or isinstance(value, Decimal):
        return value
    raise _type_error(name, value, "a decimal or None")


def _integer(values: _Values, name: str, current: int | None) -> int | None:
    if name not in values:
        return current
    value = values[name]
    if value is None or (isinstance(value, int) and not isinstance(value, bool)):
        return value
    raise _type_error(name, value, "an integer or None")


def _boolean(values: _Values, name: str, current: bool | None) -> bool | None:
    if name not in values:
        return current
    value = values[name]
    if value is None or isinstance(value, bool):
        return value
    raise _type_error(name, value, "a boolean or None")


def _labels(values: _Values, name: str, current: tuple[str, ...]) -> tuple[str, ...]:
    if name not in values:
        return current
    value = values[name]
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    raise _type_error(name, value, "a tuple of labels")


def _addresses(values: _Values, name: str, current: tuple[Pubkey, ...]) -> tuple[Pubkey, ...]:
    if name not in values:
        return current
    value = values[name]
    if isinstance(value, tuple):
        return tuple(Pubkey(str(item)) for item in value)
    raise _type_error(name, value, "a tuple of addresses")


def _structure[T](values: _Values, name: str, current: T, expected: type[T]) -> T:
    if name not in values:
        return current
    value = values[name]
    if isinstance(value, expected):
        return value
    raise _type_error(name, value, expected.__name__)


def _merge(base: TokenMetrics, patch_fields: MetricFields) -> TokenMetrics:
    """Apply the reported fields to ``base``, leaving every unreported field untouched."""
    values: dict[str, MetricValue] = dict(patch_fields)
    unknown = sorted(set(values) - _METRIC_FIELDS)
    if unknown:
        msg = f"unknown metric fields in patch: {', '.join(unknown)}"
        raise ValueError(msg)
    return TokenMetrics(
        price=_decimal(values, "price", base.price),
        price_change=_decimal(values, "price_change", base.price_change),
        volume=_decimal(values, "volume", base.volume),
        buy_volume=_decimal(values, "buy_volume", base.buy_volume),
        sell_volume=_decimal(values, "sell_volume", base.sell_volume),
        liquidity=_decimal(values, "liquidity", base.liquidity),
        slippage_bps=_decimal(values, "slippage_bps", base.slippage_bps),
        holders=_structure(values, "holders", base.holders, HolderDistribution),
        dev_transaction_count=_integer(values, "dev_transaction_count", base.dev_transaction_count),
        dev_sold=_boolean(values, "dev_sold", base.dev_sold),
        smart_wallet_transaction_count=_integer(
            values, "smart_wallet_transaction_count", base.smart_wallet_transaction_count
        ),
        smart_wallet_addresses=_addresses(
            values, "smart_wallet_addresses", base.smart_wallet_addresses
        ),
        wallet_cluster_ids=_labels(values, "wallet_cluster_ids", base.wallet_cluster_ids),
        token_state=_structure(values, "token_state", base.token_state, TokenState),
        lp_state=_structure(values, "lp_state", base.lp_state, LpState),
    )


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
            metrics=_merge(base, patch.fields),
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
