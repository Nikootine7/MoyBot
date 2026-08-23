"""Fresh-state read port (PROJECT_SPEC.md §5).

Final pre-trade validation must re-check the token "against fresh state" immediately before
acting. That requires a read that is separate from the continuous stream which produced the
decision: comparing the decision snapshot with itself can only ever conclude that nothing
changed.

This port is deliberately narrow. It is a single-token read used only at the validation
boundary, not a polling interface, so it does not weaken the event-driven principle of
PROJECT_SPEC.md §10.2. It says nothing about how a live implementation would obtain the state
(OPEN QUESTION: real data provider, docs/DECISIONS.md).

A refresh either returns state or reports that none is available. There is no third answer:
an unavailable refresh cancels (docs/DECISIONS.md D-011).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, final

from moybot.core.model.metrics import MetricFields
from moybot.core.model.primitives import Pubkey, Slot, TimestampMs
from moybot.core.state.cache_port import MetricsPatch

__all__ = [
    "RefreshResult",
    "RefreshUnavailable",
    "RefreshedState",
    "StateRefresher",
]


@final
@dataclass(frozen=True, slots=True)
class RefreshedState:
    """State read at validation time, with the point in time it was observed at.

    ``fields`` carries only what the read actually reported, exactly as for a streamed
    observation: an absent field means "not re-reported", never "zero".
    """

    mint: Pubkey
    slot: Slot
    observed_at_ms: TimestampMs
    fields: MetricFields = ()

    def to_patch(self) -> MetricsPatch:
        """Convert the refreshed fields into a cache patch."""
        return MetricsPatch(
            mint=self.mint,
            slot=self.slot,
            observed_at_ms=self.observed_at_ms,
            fields=self.fields,
        )


@final
@dataclass(frozen=True, slots=True)
class RefreshUnavailable:
    """No fresh state could be read, with the reason it could not."""

    mint: Pubkey
    reason: str


type RefreshResult = RefreshedState | RefreshUnavailable


class StateRefresher(Protocol):
    """Reads the current state of one token, on demand."""

    @property
    def name(self) -> str:
        """Stable identifier recorded in provenance."""

    def refresh(self, mint: Pubkey) -> RefreshResult:
        """Read the current state of ``mint``, or report why it is unavailable."""
