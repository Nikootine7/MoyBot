"""Weighted scorer.

Weights are configuration. An unconfigured scorer must refuse to score rather than return zero
(PROJECT_SPEC.md §9).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from moybot.core.errors import NotConfiguredError
from moybot.core.model.features import Feature, FeatureSet
from moybot.core.scoring.weighted import WeightedScorer


def _features(*pairs: tuple[str, str]) -> FeatureSet:
    return FeatureSet(
        features=tuple(
            Feature(name=name, value=Decimal(value), produced_by="test") for name, value in pairs
        )
    )


def test_unconfigured_scorer_refuses_to_score() -> None:
    scorer = WeightedScorer("test", None)
    assert not scorer.is_configured
    with pytest.raises(NotConfiguredError, match="no configured feature weights"):
        scorer.score(_features(("a", "1")))


def test_empty_weight_mapping_is_also_unconfigured() -> None:
    with pytest.raises(NotConfiguredError):
        WeightedScorer("test", {}).score(_features(("a", "1")))


def test_missing_weighted_feature_refuses_to_score() -> None:
    scorer = WeightedScorer("test", {"a": Decimal("1"), "b": Decimal("2")})
    with pytest.raises(NotConfiguredError, match="no heavy-analysis module produced it"):
        scorer.score(_features(("a", "1")))


def test_score_is_the_weighted_sum_with_contributions() -> None:
    scorer = WeightedScorer("test", {"a": Decimal("2"), "b": Decimal("0.5")})
    score = scorer.score(_features(("a", "3"), ("b", "4")))
    assert score.value == Decimal("8")
    assert score.scorer == "test"
    assert [contribution.feature for contribution in score.contributions] == ["a", "b"]
    assert [str(contribution.contribution) for contribution in score.contributions] == ["6", "2.0"]


def test_unweighted_features_do_not_contribute() -> None:
    scorer = WeightedScorer("test", {"a": Decimal("1")})
    score = scorer.score(_features(("a", "3"), ("ignored", "1000")))
    assert score.value == Decimal("3")
