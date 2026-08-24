"""Offline fresh-state reads (docs/DECISIONS.md D-009, D-010, D-011)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from moybot.adapters.replay.refresher import ReplayStateRefresher
from moybot.core.clock import SourceTimeClock
from moybot.core.errors import NotConfiguredError
from moybot.core.ingestion.refresh_port import RefreshedState, RefreshUnavailable
from moybot.core.model.primitives import Slot, TimestampMs
from tests.support import MINT_A, MINT_B, metrics, refreshed


def test_declared_state_is_returned() -> None:
    refresher = ReplayStateRefresher()
    state = refreshed(metrics(price=Decimal("2")), slot=101)
    refresher.publish(MINT_A, state)
    assert refresher.refresh(MINT_A) == state


def test_undeclared_state_is_unavailable() -> None:
    refresher = ReplayStateRefresher()
    result = refresher.refresh(MINT_A)
    assert isinstance(result, RefreshUnavailable)
    assert result.mint == MINT_A
    assert result.reason


def test_withdrawing_state_makes_it_unavailable_again() -> None:
    """State declared for one observation must not answer a later one."""
    refresher = ReplayStateRefresher()
    refresher.publish(MINT_A, refreshed())
    refresher.publish(MINT_A, None)
    assert isinstance(refresher.refresh(MINT_A), RefreshUnavailable)


def test_state_is_per_token() -> None:
    refresher = ReplayStateRefresher()
    refresher.publish(MINT_A, refreshed())
    assert isinstance(refresher.refresh(MINT_B), RefreshUnavailable)


def test_refresh_reports_its_observation_time_to_the_clock() -> None:
    clock = SourceTimeClock()
    refresher = ReplayStateRefresher(clock=clock)
    refresher.publish(MINT_A, refreshed(observed_at_ms=1_750_000_000_900))
    refresher.refresh(MINT_A)
    assert int(clock.now_ms()) == 1_750_000_000_900


def test_refreshed_state_carries_only_reported_fields() -> None:
    state = RefreshedState(
        mint=MINT_A,
        slot=Slot(101),
        observed_at_ms=TimestampMs(1_750_000_000_000),
        fields=(("price", Decimal("2")),),
    )
    assert [name for name, _ in state.fields] == ["price"]


def test_source_clock_has_no_time_before_an_observation() -> None:
    """There is no defensible substitute for an unknown time, so reading one is an error."""
    with pytest.raises(NotConfiguredError):
        SourceTimeClock().now_ms()


def test_source_clock_never_moves_backwards() -> None:
    clock = SourceTimeClock()
    clock.observe(TimestampMs(1_750_000_000_400))
    clock.observe(TimestampMs(1_750_000_000_000))
    assert int(clock.now_ms()) == 1_750_000_000_400
