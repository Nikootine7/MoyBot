"""Alerts (PROJECT_SPEC.md §2 "ACTION", docs/DECISIONS.md D-003).

Phase 1's terminal action is an alert. There is no order, no signing and no transaction type in
the domain model, because execution infrastructure and auto-buy remain undecided
(PROJECT_SPEC.md §9).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from moybot.core.model.candidate import Candidate
from moybot.core.model.decision import Decision, ValidationResult
from moybot.core.model.primitives import Pubkey, TimestampMs

__all__ = ["Alert"]


@final
@dataclass(frozen=True, slots=True)
class Alert:
    """An alert carrying the full provenance of the decision behind it."""

    correlation_id: str
    mint: Pubkey
    raised_at_ms: TimestampMs
    decision: Decision
    validation: ValidationResult
    candidate: Candidate
