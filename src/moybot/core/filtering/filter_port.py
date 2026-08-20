"""Candidate filter port (PROJECT_SPEC.md §2.4)."""

from __future__ import annotations

from typing import Protocol

from moybot.core.model.candidate import Candidate, FilterVerdict

__all__ = ["CandidateFilter"]


class CandidateFilter(Protocol):
    """A cheap check that reduces the universe before expensive analysis.

    Filters must be cheap by construction (PROJECT_SPEC.md §2.4, §10.5). Their criteria are
    configuration, never hard-coded constants (PROJECT_SPEC.md §9).
    """

    @property
    def name(self) -> str:
        """Stable identifier used in the filter trace."""

    def evaluate(self, candidate: Candidate) -> FilterVerdict:
        """Accept or reject a candidate, always with a reason on rejection."""
