"""Pre-trade validator port (PROJECT_SPEC.md §5)."""

from __future__ import annotations

from typing import Protocol

from moybot.core.model.candidate import Candidate
from moybot.core.model.decision import Decision, ValidationResult
from moybot.core.model.primitives import Slot

__all__ = ["PreTradeValidator"]


class PreTradeValidator(Protocol):
    """The last gate before an action.

    Implementations must fail closed: anything unknown, stale, or unconfigured cancels
    (PROJECT_SPEC.md §5, §10.8 — the system must never act on stale information).
    """

    def validate(
        self, candidate: Candidate, decision: Decision, current_slot: Slot
    ) -> ValidationResult:
        """Re-check volatile conditions against fresh state."""
