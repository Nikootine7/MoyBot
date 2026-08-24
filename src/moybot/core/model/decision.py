"""Strategy decisions and validation results (PROJECT_SPEC.md §5, §6, §7)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import final

from moybot.core.model.primitives import Pubkey, Slot, TimestampMs
from moybot.core.model.score import Score
from moybot.core.model.snapshot import Snapshot

__all__ = [
    "Decision",
    "DecisionOutcome",
    "RefreshAudit",
    "StalenessAudit",
    "ValidationOutcome",
    "ValidationResult",
    "VolatileComparison",
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
class RefreshAudit:
    """What the fresh-state read at validation time returned (docs/DECISIONS.md D-011)."""

    refresher: str
    available: bool
    slot: Slot | None = None
    observed_at_ms: TimestampMs | None = None
    unavailable_reason: str | None = None


@final
@dataclass(frozen=True, slots=True)
class StalenessAudit:
    """How old the refreshed state was, measured at validation time."""

    checked_at_ms: TimestampMs
    age_ms: int
    current_slot: Slot
    slot_lag: int


@final
@dataclass(frozen=True, slots=True)
class VolatileComparison:
    """One volatile field, as it stood at decision time and at validation time.

    Values are rendered exactly as strings: this is an audit record of what was compared
    (PROJECT_SPEC.md §4), not a number to compute with.
    """

    field: str
    at_decision: str
    at_validation: str


@final
@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Outcome of the final pre-trade check, with the evidence it was reached from.

    PROJECT_SPEC.md §4 requires a decision to be reconstructible, so the result carries the
    refreshed snapshot, the refresh and staleness measurements, the volatile values compared, and
    the name of the configured limit that cancelled, when one did.
    """

    outcome: ValidationOutcome
    reason: str
    checked_snapshot: Snapshot | None = None
    refresh: RefreshAudit | None = None
    staleness: StalenessAudit | None = None
    comparisons: tuple[VolatileComparison, ...] = ()
    breached_limit: str | None = None

    @property
    def passed(self) -> bool:
        """True only when validation explicitly passed."""
        return self.outcome is ValidationOutcome.PASS
