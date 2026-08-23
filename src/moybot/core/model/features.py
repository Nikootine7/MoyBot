"""Features produced by heavy analysis (PROJECT_SPEC.md §3).

Features are named exact quantities plus the name of the module that produced them, so that a
score can always be traced back to its inputs (§4, §10.9).

Phase 1 ships no feature-producing implementation: every heavy-analysis category listed in
PROJECT_SPEC.md §3 is a disabled stub (docs/DECISIONS.md D-006), so feature sets are empty
unless a test provides them.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import final

__all__ = ["Feature", "FeatureSet"]


@final
@dataclass(frozen=True, slots=True)
class Feature:
    """One named quantity produced by one heavy-analysis module."""

    name: str
    value: Decimal
    produced_by: str


@final
@dataclass(frozen=True, slots=True)
class FeatureSet:
    """All features available for one candidate."""

    features: tuple[Feature, ...] = ()

    def names(self) -> tuple[str, ...]:
        """Names of all features, in production order."""
        return tuple(feature.name for feature in self.features)

    def get(self, name: str) -> Feature | None:
        """Return the named feature, or ``None`` when it was not produced."""
        for feature in self.features:
            if feature.name == name:
                return feature
        return None
