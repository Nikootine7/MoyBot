"""Configured weighted scorer (PROJECT_SPEC.md §2, §4, §9).

Weights are never defaulted, guessed, or zero-filled. PROJECT_SPEC.md §9 lists exact scoring
weights as not final, so an unconfigured or under-configured scorer refuses to produce a score.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import final

from moybot.core.errors import NotConfiguredError
from moybot.core.model.features import FeatureSet
from moybot.core.model.score import FeatureContribution, Score

__all__ = ["WeightedScorer"]


@final
class WeightedScorer:
    """Sums ``weight * value`` over explicitly configured features."""

    def __init__(self, name: str, weights: Mapping[str, Decimal] | None) -> None:
        self._name = name
        self._weights = dict(weights) if weights else {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_configured(self) -> bool:
        return bool(self._weights)

    def score(self, features: FeatureSet) -> Score:
        """Score the feature set, or raise when configuration or inputs are incomplete."""
        if not self._weights:
            msg = (
                f"scorer {self._name!r} has no configured feature weights; scoring weights are "
                "an OPEN QUESTION (PROJECT_SPEC.md §9) and must be supplied explicitly"
            )
            raise NotConfiguredError(msg)
        contributions: list[FeatureContribution] = []
        total = Decimal(0)
        for feature_name in sorted(self._weights):
            weight = self._weights[feature_name]
            feature = features.get(feature_name)
            if feature is None:
                msg = (
                    f"scorer {self._name!r} is configured to weight feature {feature_name!r}, "
                    "but no heavy-analysis module produced it"
                )
                raise NotConfiguredError(msg)
            contribution = weight * feature.value
            total += contribution
            contributions.append(
                FeatureContribution(
                    feature=feature_name,
                    value=feature.value,
                    weight=weight,
                    contribution=contribution,
                )
            )
        return Score(value=total, scorer=self._name, contributions=tuple(contributions))
