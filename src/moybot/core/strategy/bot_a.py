"""Bot A — high probability (PROJECT_SPEC.md §6).

Bot A's question is "what is most likely to be a good opportunity?". Its distinguishing
mechanics, as stated by the specification, are hard rejection conditions evaluated before any
score is considered, and a higher confidence requirement.

Phase 1 supplies neither a rejection rule nor a threshold: both are OPEN QUESTIONS
(PROJECT_SPEC.md §9). Without a configured threshold Bot A reports ``NOT_CONFIGURED``, which
never advances a candidate.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import final

from moybot.core.errors import NotConfiguredError
from moybot.core.filtering.chain import FilterChain
from moybot.core.model.candidate import Candidate
from moybot.core.model.decision import Decision, DecisionOutcome
from moybot.core.model.features import FeatureSet
from moybot.core.scoring.scorer_port import Scorer
from moybot.core.strategy.strategy_port import HardRejectionRule

__all__ = ["BotA"]


@final
class BotA:
    """Conservative strategy: reject first, then require a configured confidence level."""

    def __init__(
        self,
        scorer: Scorer,
        filters: FilterChain,
        score_threshold: Decimal | None = None,
        hard_rejection_rules: Sequence[HardRejectionRule] = (),
    ) -> None:
        self._scorer = scorer
        self._filters = filters
        self._score_threshold = score_threshold
        self._hard_rejection_rules = tuple(hard_rejection_rules)

    @property
    def name(self) -> str:
        return "bot_a"

    @property
    def filters(self) -> FilterChain:
        return self._filters

    @property
    def hard_rejection_rule_names(self) -> tuple[str, ...]:
        return tuple(rule.name for rule in self._hard_rejection_rules)

    def evaluate(self, candidate: Candidate, features: FeatureSet) -> Decision:
        for rule in self._hard_rejection_rules:
            reason = rule.rejects(candidate, features)
            if reason is not None:
                return Decision(
                    strategy=self.name,
                    mint=candidate.mint,
                    outcome=DecisionOutcome.REJECT,
                    reason=f"hard rejection by {rule.name}: {reason}",
                )
        if self._score_threshold is None:
            return Decision(
                strategy=self.name,
                mint=candidate.mint,
                outcome=DecisionOutcome.NOT_CONFIGURED,
                reason=(
                    "no score threshold configured for bot_a; exact thresholds are an "
                    "OPEN QUESTION (PROJECT_SPEC.md §6, §9)"
                ),
            )
        try:
            score = self._scorer.score(features)
        except NotConfiguredError as exc:
            return Decision(
                strategy=self.name,
                mint=candidate.mint,
                outcome=DecisionOutcome.NOT_CONFIGURED,
                reason=str(exc),
            )
        if score.value >= self._score_threshold:
            return Decision(
                strategy=self.name,
                mint=candidate.mint,
                outcome=DecisionOutcome.ADVANCE,
                reason=f"score {score.value} met configured threshold {self._score_threshold}",
                score=score,
            )
        return Decision(
            strategy=self.name,
            mint=candidate.mint,
            outcome=DecisionOutcome.REJECT,
            reason=f"score {score.value} below configured threshold {self._score_threshold}",
            score=score,
        )
