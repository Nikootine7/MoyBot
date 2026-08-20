"""Heavy-analysis module port (PROJECT_SPEC.md §3)."""

from __future__ import annotations

from typing import Protocol

from moybot.core.model.candidate import Candidate
from moybot.core.model.features import Feature

__all__ = ["HeavyAnalysisModule"]


class HeavyAnalysisModule(Protocol):
    """Expensive analysis reserved for candidates.

    PROJECT_SPEC.md §3 lists heavy-analysis *categories*, explicitly not implementations or
    dependencies. Phase 1 therefore registers the categories and implements none of them.
    """

    @property
    def name(self) -> str:
        """Stable identifier used in configuration, features and provenance."""

    def analyze(self, candidate: Candidate) -> tuple[Feature, ...]:
        """Produce features for a candidate."""
