"""Event detection.

Phase 1 detectors must surface only what a source declared, so that no detection threshold is
implied (PROJECT_SPEC.md §2.2, docs/DECISIONS.md D-004).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from moybot.core.events.registry import DeclaredEventDetector, EventDetectorRegistry
from moybot.core.model.event import Event, parse_event_kind
from moybot.core.model.metrics import MetricValue
from moybot.core.model.primitives import Slot, TimestampMs
from moybot.core.model.update import MarketUpdate
from tests.support import MINT_A


def _update(*events: Event, **fields: MetricValue) -> MarketUpdate:
    return MarketUpdate(
        mint=MINT_A,
        slot=Slot(100),
        observed_at_ms=TimestampMs(1_750_000_000_000),
        source="test",
        sequence=0,
        metrics=tuple(fields.items()),
        declared_events=events,
    )


def _event(kind: str = "smart_wallet_buy") -> Event:
    return Event(
        kind=parse_event_kind(kind),
        mint=MINT_A,
        slot=Slot(100),
        timestamp_ms=TimestampMs(1_750_000_000_000),
        source="test",
    )


def test_declared_events_are_surfaced() -> None:
    event = _event()
    assert DeclaredEventDetector().detect(_update(event)) == (event,)


def test_large_metric_moves_alone_produce_no_event() -> None:
    update = _update(price=Decimal("1000000"), volume=Decimal("999999999"))
    assert DeclaredEventDetector().detect(update) == ()


def test_registry_concatenates_detectors_in_order() -> None:
    event = _event()
    registry = EventDetectorRegistry([DeclaredEventDetector(), DeclaredEventDetector()])
    assert registry.detect(_update(event)) == (event, event)
    assert registry.detector_names == ("declared_events", "declared_events")


def test_event_kind_is_an_open_label() -> None:
    assert parse_event_kind("some_future_event_type") == "some_future_event_type"


def test_event_kind_must_not_be_blank() -> None:
    with pytest.raises(ValueError, match="non-empty label"):
        parse_event_kind("   ")
