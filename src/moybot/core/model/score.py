"""Scores (PROJECT_SPEC.md §2, §4).

A score is never a bare number: it carries the per-feature contributions that produced it, so
that the reasoning behind a decision is reconstructible.

Scoring weights and thresholds are OPEN QUESTIONS (PROJECT_SPEC.md §9). Nothing in this module
supplies one.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import final

__all__ = ["FeatureContribution", "Score"]


@final
@dataclass(frozen=True, slots=True)
class FeatureContribution:
    """How one feature contributed to a score."""

    feature: str
    value: Decimal
    weight: Decimal
    contribution: Decimal


@final
@dataclass(frozen=True, slots=True)
class Score:
    """A score together with its full derivation."""

    value: Decimal
    scorer: str
    contributions: tuple[FeatureContribution, ...] = ()
