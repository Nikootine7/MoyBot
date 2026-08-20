"""Snapshot construction and immutability."""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from moybot.core.model.primitives import Slot, TimestampMs
from moybot.core.snapshots.builder import SnapshotBuilder
from moybot.core.state.cache_port import MetricsPatch
from moybot.core.state.memory_cache import InMemoryStateCache
from tests.support import MINT_A


def _cache_with_price() -> InMemoryStateCache:
    cache = InMemoryStateCache()
    cache.apply(
        MetricsPatch(
            mint=MINT_A,
            slot=Slot(100),
            observed_at_ms=TimestampMs(1_750_000_000_000),
            fields=(("price", Decimal("1.5")),),
        )
    )
    return cache


def test_capture_returns_none_for_never_observed_token() -> None:
    builder = SnapshotBuilder(InMemoryStateCache())
    assert builder.capture(MINT_A, Slot(100)) is None


def test_capture_defaults_to_the_observation_time() -> None:
    builder = SnapshotBuilder(_cache_with_price())
    captured = builder.capture(MINT_A, Slot(101))
    assert captured is not None
    assert captured.captured_at_ms == TimestampMs(1_750_000_000_000)


def test_explicit_capture_time_overrides_the_observation_time() -> None:
    builder = SnapshotBuilder(_cache_with_price())
    captured = builder.capture(MINT_A, Slot(101), TimestampMs(1_750_000_000_250))
    assert captured is not None
    assert captured.captured_at_ms == TimestampMs(1_750_000_000_250)


def test_sequence_is_monotonic() -> None:
    builder = SnapshotBuilder(_cache_with_price())
    first = builder.capture(MINT_A, Slot(100))
    second = builder.capture(MINT_A, Slot(100))
    assert first is not None
    assert second is not None
    assert (first.sequence, second.sequence) == (0, 1)


def test_snapshot_is_immutable() -> None:
    builder = SnapshotBuilder(_cache_with_price())
    captured = builder.capture(MINT_A, Slot(100))
    assert captured is not None
    with pytest.raises(dataclasses.FrozenInstanceError):
        captured.slot = Slot(999)  # type: ignore[misc]


def test_age_and_slot_lag() -> None:
    builder = SnapshotBuilder(_cache_with_price())
    captured = builder.capture(MINT_A, Slot(100))
    assert captured is not None
    assert captured.age_ms(TimestampMs(1_750_000_000_400)) == 400
    assert captured.slot_lag(Slot(107)) == 7
