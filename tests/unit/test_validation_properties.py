"""Property-based final-validation tests (PROJECT_SPEC.md §5).

Two invariants matter regardless of any limit: re-reading fresh state must not rewrite the state
the decision was made on, and a stricter limit must never admit something a looser one refused.
The limits below are test inputs, not domain decisions.
"""

from __future__ import annotations

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from moybot.core.clock import FixedClock
from moybot.core.model.decision import Decision, DecisionOutcome, ValidationOutcome
from moybot.core.model.metrics import TokenMetrics
from moybot.core.model.primitives import Slot, TimestampMs
from moybot.core.snapshots.builder import SnapshotBuilder
from moybot.core.state.memory_cache import InMemoryStateCache
from moybot.core.validation.material_deterioration import (
    DeteriorationPolicy,
    MaterialDeteriorationValidator,
    StalenessPolicy,
)
from tests.support import MINT_A, StubRefresher, candidate, metrics, refreshed, snapshot

_AT_MS = 1_750_000_000_000
_SLOT = 100
_STALENESS = StalenessPolicy(max_snapshot_age_ms=1_000, max_slot_lag=5)
_DECISION = Decision(
    strategy="test", mint=MINT_A, outcome=DecisionOutcome.ADVANCE, reason="test decision"
)

_amounts = st.decimals(
    min_value=Decimal("0"), max_value=Decimal("10000"), allow_nan=False, allow_infinity=False
)
_positive_amounts = st.decimals(
    min_value=Decimal("0.01"), max_value=Decimal("10000"), allow_nan=False, allow_infinity=False
)
_fractions = st.decimals(
    min_value=Decimal("0"), max_value=Decimal("1"), allow_nan=False, allow_infinity=False
)


@st.composite
def _scenarios(draw: st.DrawFn) -> tuple[TokenMetrics, TokenMetrics]:
    """Metrics at decision time and at validation time, all volatile fields known."""
    at_decision = metrics(
        price=draw(_positive_amounts),
        liquidity=draw(_positive_amounts),
        slippage_bps=draw(_amounts),
        buy_volume=draw(_positive_amounts),
        sell_volume=draw(_amounts),
    )
    at_validation = metrics(
        price=draw(_positive_amounts),
        liquidity=draw(_positive_amounts),
        slippage_bps=draw(_amounts),
        buy_volume=draw(_positive_amounts),
        sell_volume=draw(_amounts),
        dev_sold=draw(st.booleans()),
    )
    return at_decision, at_validation


def _validate(
    at_decision: TokenMetrics,
    at_validation: TokenMetrics,
    policy: DeteriorationPolicy,
) -> ValidationOutcome:
    cache = InMemoryStateCache()
    validator = MaterialDeteriorationValidator(
        builder=SnapshotBuilder(cache),
        cache=cache,
        clock=FixedClock(TimestampMs(_AT_MS)),
        refresher=StubRefresher(refreshed(at_validation, slot=_SLOT, observed_at_ms=_AT_MS)),
        staleness_policy=_STALENESS,
        deterioration_policy=policy,
    )
    decided = candidate(snapshot(slot=_SLOT, captured_at_ms=_AT_MS, token_metrics=at_decision))
    return validator.validate(decided, _DECISION, Slot(_SLOT)).outcome


@given(_scenarios())
def test_refreshing_never_rewrites_the_decision_snapshot(
    scenario: tuple[TokenMetrics, TokenMetrics],
) -> None:
    at_decision, at_validation = scenario
    cache = InMemoryStateCache()
    validator = MaterialDeteriorationValidator(
        builder=SnapshotBuilder(cache),
        cache=cache,
        clock=FixedClock(TimestampMs(_AT_MS)),
        refresher=StubRefresher(refreshed(at_validation, slot=_SLOT, observed_at_ms=_AT_MS)),
        staleness_policy=_STALENESS,
        deterioration_policy=DeteriorationPolicy(
            max_price_drop_fraction=Decimal("1"),
            max_liquidity_drop_fraction=Decimal("1"),
            max_slippage_bps=Decimal("100000"),
            max_sell_pressure_ratio=Decimal("100000"),
            cancel_on_dev_sold=False,
            cancel_on_smart_wallet_exit=False,
            cancel_on_lp_supply_change=False,
        ),
    )
    decided = candidate(snapshot(slot=_SLOT, captured_at_ms=_AT_MS, token_metrics=at_decision))
    validator.validate(decided, _DECISION, Slot(_SLOT))
    assert decided.snapshot.metrics == at_decision


@given(_scenarios(), _fractions, _fractions, _amounts, _amounts, _fractions, _fractions)
def test_tightening_a_limit_never_turns_a_cancellation_into_a_pass(
    scenario: tuple[TokenMetrics, TokenMetrics],
    price_limit: Decimal,
    liquidity_limit: Decimal,
    slippage_limit: Decimal,
    sell_pressure_limit: Decimal,
    price_tightening: Decimal,
    liquidity_tightening: Decimal,
) -> None:
    at_decision, at_validation = scenario
    looser = DeteriorationPolicy(
        max_price_drop_fraction=price_limit,
        max_liquidity_drop_fraction=liquidity_limit,
        max_slippage_bps=slippage_limit,
        max_sell_pressure_ratio=sell_pressure_limit,
        cancel_on_dev_sold=False,
        cancel_on_smart_wallet_exit=False,
        cancel_on_lp_supply_change=False,
    )
    tighter = DeteriorationPolicy(
        max_price_drop_fraction=price_limit * price_tightening,
        max_liquidity_drop_fraction=liquidity_limit * liquidity_tightening,
        max_slippage_bps=slippage_limit / 2,
        max_sell_pressure_ratio=sell_pressure_limit / 2,
        cancel_on_dev_sold=True,
        cancel_on_smart_wallet_exit=True,
        cancel_on_lp_supply_change=True,
    )
    if _validate(at_decision, at_validation, looser) is ValidationOutcome.CANCELLED:
        assert _validate(at_decision, at_validation, tighter) is ValidationOutcome.CANCELLED
