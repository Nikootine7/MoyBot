"""Structured-log alert sink (docs/DECISIONS.md D-003)."""

from __future__ import annotations

from typing import final

import structlog

from moybot.core.model.alert import Alert
from moybot.core.serialization import to_json_value

__all__ = ["CollectingAlertSink", "LogAlertSink"]


@final
class LogAlertSink:
    """Emits alerts as structured stdout log records.

    External alert destinations are an OPEN QUESTION; nothing here sends over a network.
    """

    def __init__(self) -> None:
        self._logger = structlog.get_logger("moybot.alert")

    @property
    def name(self) -> str:
        return "log_alert_sink"

    def emit(self, alert: Alert) -> None:
        self._logger.info(
            "alert_raised",
            correlation_id=alert.correlation_id,
            mint=alert.mint,
            strategy=alert.decision.strategy,
            raised_at_ms=int(alert.raised_at_ms),
            decision=to_json_value(alert.decision),
            validation=to_json_value(alert.validation),
        )


@final
class CollectingAlertSink:
    """Collects alerts in memory, for tests and dry runs."""

    def __init__(self) -> None:
        self.alerts: list[Alert] = []

    @property
    def name(self) -> str:
        return "collecting_alert_sink"

    def emit(self, alert: Alert) -> None:
        self.alerts.append(alert)
