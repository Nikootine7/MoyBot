"""Bot B — black swan / early opportunity (PROJECT_SPEC.md §7).

Bot B's question is "what might be extremely early, before most of the market has noticed it?".
The specification is explicit that Bot B is not Bot A with a lower threshold, so this
implementation intentionally does not reuse Bot A's mechanics: it has no hard-rejection stage
and no confirmation requirement, and it requires its own separately configured gate.

Which early signals Bot B should weigh (first smart-wallet activity, wallet growth, transaction
velocity, funding patterns, early liquidity, social acceleration, novelty, absence of rug
indicators, upside versus downside) is listed in §7 as *potentially important*, and every
criterion behind them is an OPEN QUESTION (§9). Phase 1 therefore configures nothing and reports
``NOT_CONFIGURED``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import final

from moybot.core.errors import NotConfiguredError
from moybot.core.filtering.chain import FilterChain
from moybot.core.model.candidate import Candidate
from moybot.core.model.decision import Decision, DecisionOutcome
from moybot.core.model.features import FeatureSet
from moybot.core.scoring.scorer_port import Scorer

__all__ = ["BotB"]


@final
class BotB:
    """Early-opportunity strategy with its own filters, scorer and gate."""

    def __init__(
        self,
        scorer: Scorer,
        filters: FilterChain,
        score_threshold: Decimal | None = None,
    ) -> None:
        self._scorer = scorer
        self._filters = filters
        self._score_threshold = score_threshold

    @property
    def name(self) -> str:
        return "bot_b"

    @property
    def filters(self) -> FilterChain:
        return self._filters

    def evaluate(self, candidate: Candidate, features: FeatureSet) -> Decision:
        if self._score_threshold is None:
            return Decision(
                strategy=self.name,
                mint=candidate.mint,
                outcome=DecisionOutcome.NOT_CONFIGURED,
                reason=(
                    "no score threshold configured for bot_b; Bot B's gate is independent of "
                    "Bot A's and is an OPEN QUESTION (PROJECT_SPEC.md §7, §9)"
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
