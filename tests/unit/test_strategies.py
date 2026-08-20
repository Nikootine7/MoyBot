"""Bot A and Bot B.

The thresholds used here are test inputs. Neither strategy ships one, and neither may fall back
to a default (PROJECT_SPEC.md §6, §7, §9).
"""

from __future__ import annotations

from decimal import Decimal

from moybot.core.filtering.accept_all import AcceptAllFilter
from moybot.core.filtering.chain import FilterChain
from moybot.core.model.decision import DecisionOutcome
from moybot.core.model.features import Feature, FeatureSet
from moybot.core.scoring.weighted import WeightedScorer
from moybot.core.strategy.bot_a import BotA
from moybot.core.strategy.bot_b import BotB
from tests.support import StubRejectionRule, candidate

_FEATURES = FeatureSet(
    features=(Feature(name="test_feature", value=Decimal("10"), produced_by="test"),)
)
_WEIGHTS = {"test_feature": Decimal("1")}


def _chain() -> FilterChain:
    return FilterChain([AcceptAllFilter()])


def test_bot_a_without_threshold_is_not_configured() -> None:
    bot = BotA(scorer=WeightedScorer("bot_a", _WEIGHTS), filters=_chain())
    decision = bot.evaluate(candidate(), _FEATURES)
    assert decision.outcome is DecisionOutcome.NOT_CONFIGURED
    assert "OPEN QUESTION" in decision.reason


def test_bot_a_without_weights_is_not_configured() -> None:
    bot = BotA(scorer=WeightedScorer("bot_a", None), filters=_chain(), score_threshold=Decimal("5"))
    decision = bot.evaluate(candidate(), _FEATURES)
    assert decision.outcome is DecisionOutcome.NOT_CONFIGURED
    assert decision.score is None


def test_bot_a_advances_when_the_configured_threshold_is_met() -> None:
    bot = BotA(
        scorer=WeightedScorer("bot_a", _WEIGHTS), filters=_chain(), score_threshold=Decimal("10")
    )
    decision = bot.evaluate(candidate(), _FEATURES)
    assert decision.outcome is DecisionOutcome.ADVANCE
    assert decision.score is not None
    assert decision.score.value == Decimal("10")


def test_bot_a_rejects_below_the_configured_threshold() -> None:
    bot = BotA(
        scorer=WeightedScorer("bot_a", _WEIGHTS), filters=_chain(), score_threshold=Decimal("11")
    )
    assert bot.evaluate(candidate(), _FEATURES).outcome is DecisionOutcome.REJECT


def test_bot_a_hard_rejection_runs_before_scoring() -> None:
    bot = BotA(
        scorer=WeightedScorer("bot_a", None),
        filters=_chain(),
        score_threshold=Decimal("1"),
        hard_rejection_rules=(StubRejectionRule("test_rule", "unacceptable"),),
    )
    decision = bot.evaluate(candidate(), _FEATURES)
    assert decision.outcome is DecisionOutcome.REJECT
    assert "hard rejection by test_rule" in decision.reason


def test_bot_a_ships_no_hard_rejection_rule() -> None:
    bot = BotA(scorer=WeightedScorer("bot_a", _WEIGHTS), filters=_chain())
    assert bot.hard_rejection_rule_names == ()


def test_bot_b_without_threshold_is_not_configured() -> None:
    bot = BotB(scorer=WeightedScorer("bot_b", _WEIGHTS), filters=_chain())
    decision = bot.evaluate(candidate(), _FEATURES)
    assert decision.outcome is DecisionOutcome.NOT_CONFIGURED


def test_bot_b_gate_is_independent_of_bot_a() -> None:
    threshold = Decimal("10")
    bot_a = BotA(
        scorer=WeightedScorer("bot_a", _WEIGHTS), filters=_chain(), score_threshold=threshold
    )
    bot_b = BotB(scorer=WeightedScorer("bot_b", _WEIGHTS), filters=_chain())
    assert bot_a.evaluate(candidate(), _FEATURES).outcome is DecisionOutcome.ADVANCE
    assert bot_b.evaluate(candidate(), _FEATURES).outcome is DecisionOutcome.NOT_CONFIGURED


def test_strategies_have_distinct_names_and_own_filters() -> None:
    chain_a = _chain()
    chain_b = FilterChain([])
    bot_a = BotA(scorer=WeightedScorer("bot_a", _WEIGHTS), filters=chain_a)
    bot_b = BotB(scorer=WeightedScorer("bot_b", _WEIGHTS), filters=chain_b)
    assert (bot_a.name, bot_b.name) == ("bot_a", "bot_b")
    assert bot_a.filters is chain_a
    assert bot_b.filters is chain_b
