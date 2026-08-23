"""Strategy port (PROJECT_SPEC.md §6, §7)."""

from __future__ import annotations

from typing import Protocol

from moybot.core.filtering.chain import FilterChain
from moybot.core.model.candidate import Candidate
from moybot.core.model.decision import Decision
from moybot.core.model.features import FeatureSet

__all__ = ["HardRejectionRule", "Strategy"]


class Strategy(Protocol):
    """A detection philosophy with its own filters, scorer and gate.

    Each strategy owns its candidate filters so that the two bots can look at the universe
    differently rather than sharing one funnel.
    """

    @property
    def name(self) -> str:
        """Stable identifier recorded on every decision."""

    @property
    def filters(self) -> FilterChain:
        """The strategy's own cheap filter chain (PROJECT_SPEC.md §2.4)."""

    def evaluate(self, candidate: Candidate, features: FeatureSet) -> Decision:
        """Decide whether the candidate should advance to pre-trade validation."""


class HardRejectionRule(Protocol):
    """A condition that rejects a candidate outright (PROJECT_SPEC.md §6).

    Phase 1 ships none: the rejection criteria (rug indicators, wallet dominance, cluster risk)
    are OPEN QUESTIONS in PROJECT_SPEC.md §9.
    """

    @property
    def name(self) -> str:
        """Stable identifier recorded in the decision reason."""

    def rejects(self, candidate: Candidate, features: FeatureSet) -> str | None:
        """Return a rejection reason, or ``None`` when the rule does not reject."""
