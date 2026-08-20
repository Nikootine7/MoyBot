"""Scorer port (PROJECT_SPEC.md §2, §4)."""

from __future__ import annotations

from typing import Protocol

from moybot.core.model.features import FeatureSet
from moybot.core.model.score import Score

__all__ = ["Scorer"]


class Scorer(Protocol):
    """Turns features into a score plus its derivation."""

    @property
    def name(self) -> str:
        """Stable identifier recorded on every score."""

    def score(self, features: FeatureSet) -> Score:
        """Score a feature set.

        Implementations must raise ``NotConfiguredError`` rather than substituting a default when
        a required weight is missing (PROJECT_SPEC.md §9).
        """
