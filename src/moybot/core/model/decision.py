"""Strategy decisions and validation results (PROJECT_SPEC.md §5, §6, §7)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import final

from moybot.core.model.primitives import Pubkey
from moybot.core.model.score import Score
from moybot.core.model.snapshot import Snapshot

__all__ = [
    "Decision",
    "DecisionOutcome",
    "ValidationOutcome",
    "ValidationResult",
]


class DecisionOutcome(StrEnum):
    """What a strategy concluded about a candidate."""

    ADVANCE = "advance"
    """The candidate passes the strategy's own gate and proceeds to pre-trade validation."""

    REJECT = "reject"
    """The candidate does not pass the strategy's gate."""

    NOT_CONFIGURED = "not_configured"
    """The strategy cannot decide because a required, undecided value is missing.

    PROJECT_SPEC.md §9 leaves thresholds and weights open. Rather than inventing one, the
    strategy reports that it is not configured, which never advances a candidate.
    """


class ValidationOutcome(StrEnum):
    """Result of the final pre-trade validation (PROJECT_SPEC.md §5)."""

    PASS = "pass"
    CANCELLED = "cancelled"


@final
@dataclass(frozen=True, slots=True)
class Decision:
    """One strategy's conclusion about one candidate."""

    strategy: str
    mint: Pubkey
    outcome: DecisionOutcome
    reason: str
    score: Score | None = None


@final
@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Outcome of the final pre-trade check, with the snapshot it was checked against."""

    outcome: ValidationOutcome
    reason: str
    checked_snapshot: Snapshot | None = None

    @property
    def passed(self) -> bool:
        """True only when validation explicitly passed."""
        return self.outcome is ValidationOutcome.PASS
