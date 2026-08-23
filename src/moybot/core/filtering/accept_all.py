"""Pass-through filter."""

from __future__ import annotations

from typing import final

from moybot.core.model.candidate import Candidate, FilterVerdict

__all__ = ["AcceptAllFilter"]


@final
class AcceptAllFilter:
    """Accepts every candidate.

    Phase 1's default filter. PROJECT_SPEC.md §2.4 states that the reduction funnel is an
    architectural principle rather than a hardcoded requirement, and §9 leaves every filter
    criterion open, so the default must not reject anything on invented grounds.
    """

    @property
    def name(self) -> str:
        return "accept_all"

    def evaluate(self, candidate: Candidate) -> FilterVerdict:
        del candidate
        return FilterVerdict(filter_name=self.name, accepted=True)
