"""Filter chain (PROJECT_SPEC.md §2.4)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import final

from moybot.core.filtering.filter_port import CandidateFilter
from moybot.core.model.candidate import Candidate, FilterVerdict

__all__ = ["FilterChain", "FilterChainResult"]


@final
@dataclass(frozen=True, slots=True)
class FilterChainResult:
    """Outcome of running a filter chain, including the full trace."""

    accepted: bool
    candidate: Candidate
    trace: tuple[FilterVerdict, ...]
    rejected_by: str | None = None


@final
class FilterChain:
    """Runs filters in order and stops at the first rejection.

    Short-circuiting is the point: the chain exists to avoid spending work on candidates that a
    cheaper check has already excluded (PROJECT_SPEC.md §10.5).
    """

    def __init__(self, filters: Sequence[CandidateFilter]) -> None:
        self._filters = tuple(filters)

    @property
    def filter_names(self) -> tuple[str, ...]:
        return tuple(candidate_filter.name for candidate_filter in self._filters)

    def run(self, candidate: Candidate) -> FilterChainResult:
        trace: list[FilterVerdict] = []
        for candidate_filter in self._filters:
            verdict = candidate_filter.evaluate(candidate)
            trace.append(verdict)
            if not verdict.accepted:
                return FilterChainResult(
                    accepted=False,
                    candidate=replace(candidate, filter_trace=tuple(trace)),
                    trace=tuple(trace),
                    rejected_by=verdict.filter_name,
                )
        return FilterChainResult(
            accepted=True,
            candidate=replace(candidate, filter_trace=tuple(trace)),
            trace=tuple(trace),
        )
