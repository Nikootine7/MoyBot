"""Alert sinks and serialization."""

from __future__ import annotations

from decimal import Decimal

import pytest

from moybot.core.action.log_sink import CollectingAlertSink
from moybot.core.model.alert import Alert
from moybot.core.model.decision import (
    Decision,
    DecisionOutcome,
    ValidationOutcome,
    ValidationResult,
)
from moybot.core.model.primitives import TimestampMs
from moybot.core.serialization import to_json_value
from tests.support import MINT_A, candidate, snapshot


def _alert() -> Alert:
    return Alert(
        correlation_id="corr:0:0",
        mint=MINT_A,
        raised_at_ms=TimestampMs(1_750_000_000_000),
        decision=Decision(
            strategy="test", mint=MINT_A, outcome=DecisionOutcome.ADVANCE, reason="test"
        ),
        validation=ValidationResult(
            outcome=ValidationOutcome.PASS, reason="fresh", checked_snapshot=snapshot()
        ),
        candidate=candidate(),
    )


def test_collecting_sink_keeps_alerts() -> None:
    sink = CollectingAlertSink()
    alert = _alert()
    sink.emit(alert)
    assert sink.alerts == [alert]
    assert sink.name == "collecting_alert_sink"


def test_alert_serializes_losslessly() -> None:
    payload = to_json_value(_alert())
    assert isinstance(payload, dict)
    assert payload["decision"] == {
        "strategy": "test",
        "mint": MINT_A,
        "outcome": "advance",
        "reason": "test",
        "score": None,
    }


def test_decimals_serialize_as_exact_strings() -> None:
    assert to_json_value(Decimal("0.00000410")) == "0.00000410"


def test_unserializable_value_is_rejected() -> None:
    with pytest.raises(TypeError, match="cannot serialize value"):
        to_json_value(object())
