"""Continuous state cache."""

from __future__ import annotations

from decimal import Decimal

import pytest

from moybot.core.model.metrics import MetricValue, WalletActivity, WalletHistory
from moybot.core.model.primitives import Slot, TimestampMs
from moybot.core.state.cache_port import MetricsPatch
from moybot.core.state.memory_cache import InMemoryStateCache
from tests.support import MINT_A, WALLET_A


def _patch(slot: int, **fields: MetricValue) -> MetricsPatch:
    return MetricsPatch(
        mint=MINT_A,
        slot=Slot(slot),
        observed_at_ms=TimestampMs(1_750_000_000_000 + slot),
        fields=tuple(fields.items()),
    )


def test_unknown_token_is_none() -> None:
    assert InMemoryStateCache().get(MINT_A) is None


def test_patch_merges_only_reported_fields() -> None:
    cache = InMemoryStateCache()
    cache.apply(_patch(1, price=Decimal("2"), liquidity=Decimal("500")))
    cached = cache.apply(_patch(2, price=Decimal("3")))
    assert cached.metrics.price == Decimal("3")
    assert cached.metrics.liquidity == Decimal("500")
    assert cached.last_slot == Slot(2)


def test_unreported_field_stays_unknown_rather_than_zero() -> None:
    cache = InMemoryStateCache()
    cached = cache.apply(_patch(1, price=Decimal("2")))
    assert cached.metrics.volume is None


def test_explicit_none_clears_a_field() -> None:
    cache = InMemoryStateCache()
    cache.apply(_patch(1, price=Decimal("2")))
    cached = cache.apply(_patch(2, price=None))
    assert cached.metrics.price is None


def test_unknown_metric_field_is_rejected() -> None:
    cache = InMemoryStateCache()
    with pytest.raises(ValueError, match="unknown metric fields"):
        cache.apply(_patch(1, moon_phase=None))


def test_value_of_the_wrong_type_is_rejected() -> None:
    """A reported value the domain model cannot hold is refused, not coerced or written."""
    cache = InMemoryStateCache()
    with pytest.raises(TypeError, match="expects a decimal or None"):
        cache.apply(_patch(1, price=True))


def test_wallet_history_round_trip() -> None:
    cache = InMemoryStateCache()
    history = WalletHistory(
        wallet=WALLET_A,
        activity=(
            WalletActivity(
                wallet=WALLET_A,
                mint=MINT_A,
                direction="buy",  # type: ignore[arg-type]
                slot=Slot(1),
                timestamp_ms=TimestampMs(1_750_000_000_000),
            ),
        ),
    )
    cache.record_wallet_history(history)
    assert cache.wallet_history(WALLET_A) == history
    assert cache.wallet_history(MINT_A) is None


def test_tracked_mints_reflects_applied_patches() -> None:
    cache = InMemoryStateCache()
    cache.apply(_patch(1, price=Decimal("2")))
    assert cache.tracked_mints() == (MINT_A,)
