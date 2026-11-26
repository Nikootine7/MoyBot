"""User-facing CLI message catalog.

Structured event names, fields, decision reasons, and provenance remain language-neutral.
"""

from __future__ import annotations

from typing import Literal

from moybot.core.model.alert import Alert
from moybot.core.model.decision import DecisionOutcome, ValidationOutcome

__all__ = ["Language", "alert_message", "replay_completed_message"]

Language = Literal["en", "fa"]

_DECISION_MESSAGES: dict[Language, dict[DecisionOutcome, str]] = {
    "en": {
        DecisionOutcome.ADVANCE: "candidate advanced",
        DecisionOutcome.REJECT: "candidate rejected",
        DecisionOutcome.NOT_CONFIGURED: "decision not configured",
    },
    "fa": {
        DecisionOutcome.ADVANCE: "نامزد برای ادامه تأیید شد",
        DecisionOutcome.REJECT: "نامزد رد شد",
        DecisionOutcome.NOT_CONFIGURED: "تصمیم‌گیری به‌دلیل تنظیم‌نبودن معیارها ممکن نیست",
    },
}

_VALIDATION_MESSAGES: dict[Language, dict[ValidationOutcome, str]] = {
    "en": {
        ValidationOutcome.PASS: "passed",
        ValidationOutcome.CANCELLED: "cancelled",
    },
    "fa": {
        ValidationOutcome.PASS: "موفق بود",
        ValidationOutcome.CANCELLED: "لغو شد",
    },
}


def replay_completed_message(language: Language) -> str:
    """Return the localized human-readable replay summary."""
    if language == "fa":
        return "اجرای بازپخش به پایان رسید."
    return "Replay completed."


def alert_message(alert: Alert, language: Language) -> str:
    """Summarize an alert in the selected language without changing its audit data."""
    decision = _DECISION_MESSAGES[language][alert.decision.outcome]
    validation = _VALIDATION_MESSAGES[language][alert.validation.outcome]
    if language == "fa":
        return f"هشدار موی‌بات: {decision}؛ اعتبارسنجی {validation}."
    return f"MOYBOT alert: {decision}; validation {validation}."
