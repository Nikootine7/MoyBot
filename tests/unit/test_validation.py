"""Final pre-trade validation.

The limits below are test inputs. The shipped validator has none and cancels everything until it
is configured (PROJECT_SPEC.md §5, §9, §10.8).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from moybot.core.clock import FixedClock
from moybot.core.model.decision import Decision, DecisionOutcome, ValidationOutcome
from moybot.core.model.metrics import LpState, TokenMetrics
from moybot.core.model.primitives import Slot, TimestampMs
from moybot.core.snapshots.builder import SnapshotBuilder
from moybot.core.state.cache_port import MetricsPatch
from moybot.core.state.memory_cache import InMemoryStateCache
from moybot.core.validation.material_deterioration import (
    DeteriorationPolicy,
    MaterialDeteriorationValidator,
    StalenessPolicy,
)
from tests.support import MINT_A, WALLET_A, WALLET_B, candidate, metrics, snapshot

_STALENESS = StalenessPolicy(max_snapshot_age_ms=1_000, max_slot_lag=5)
_DETERIORATION = DeteriorationPolicy(
    max_price_drop_fraction=Decimal("0.1"),
    max_liquidity_drop_fraction=Decimal("0.1"),
    max_slippage_bps=Decimal("100"),
    max_sell_pressure_ratio=Decimal("2"),
    cancel_on_dev_sold=True,
    cancel_on_smart_wallet_exit=True,
    cancel_on_lp_supply_change=True,
)
_DECISION = Decision(
    strategy="test", mint=MINT_A, outcome=DecisionOutcome.ADVANCE, reason="test decision"
)


def _cache(fresh: TokenMetrics) -> InMemoryStateCache:
    cache = InMemoryStateCache()
    cache.apply(
        MetricsPatch(
            mint=MINT_A,
            slot=Slot(100),
            observed_at_ms=TimestampMs(1_750_000_000_000),
            fields=tuple(
                (field, value)
                for field, value in (
                    ("price", fresh.price),
                    ("price_change", fresh.price_change),
                    ("volume", fresh.volume),
                    ("buy_volume", fresh.buy_volume),
                    ("sell_volume", fresh.sell_volume),
                    ("liquidity", fresh.liquidity),
                    ("slippage_bps", fresh.slippage_bps),
                    ("holders", fresh.holders),
                    ("dev_transaction_count", fresh.dev_transaction_count),
                    ("dev_sold", fresh.dev_sold),
                    ("smart_wallet_transaction_count", fresh.smart_wallet_transaction_count),
                    ("smart_wallet_addresses", fresh.smart_wallet_addresses),
                    ("wallet_cluster_ids", fresh.wallet_cluster_ids),
                    ("token_state", fresh.token_state),
                    ("lp_state", fresh.lp_state),
                )
            ),
        )
    )
    return cache


def _validator(
    cache: InMemoryStateCache,
    clock: FixedClock,
    staleness: StalenessPolicy | None = _STALENESS,
    deterioration: DeteriorationPolicy | None = _DETERIORATION,
) -> MaterialDeteriorationValidator:
    return MaterialDeteriorationValidator(
        builder=SnapshotBuilder(cache),
        clock=clock,
        staleness_policy=staleness,
        deterioration_policy=deterioration,
    )


def test_unconfigured_validator_cancels(clock: FixedClock) -> None:
    validator = _validator(_cache(metrics()), clock, staleness=None, deterioration=None)
    assert not validator.is_configured
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "staleness policy not configured" in result.reason


def test_missing_deterioration_policy_cancels(clock: FixedClock) -> None:
    validator = _validator(_cache(metrics()), clock, deterioration=None)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "deterioration policy not configured" in result.reason


def test_missing_fresh_state_cancels(clock: FixedClock) -> None:
    validator = _validator(InMemoryStateCache(), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "no fresh snapshot" in result.reason


def test_stale_observation_cancels(clock: FixedClock) -> None:
    validator = _validator(_cache(metrics()), clock)
    clock.advance_ms(_STALENESS.max_snapshot_age_ms + 1)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "ms old" in result.reason


def test_slot_lag_cancels(clock: FixedClock) -> None:
    validator = _validator(_cache(metrics()), clock)
    result = validator.validate(candidate(), _DECISION, Slot(200))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "slots behind" in result.reason


def test_unknown_volatile_field_in_decision_snapshot_cancels(clock: FixedClock) -> None:
    validator = _validator(_cache(metrics()), clock)
    stale_candidate = candidate(current=snapshot(token_metrics=metrics(slippage_bps=None)))
    result = validator.validate(stale_candidate, _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "volatile fields unknown in the decision snapshot: slippage_bps" in result.reason


def test_unknown_volatile_field_at_validation_time_cancels(clock: FixedClock) -> None:
    validator = _validator(_cache(metrics(dev_sold=None)), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "volatile fields unknown at validation time: dev_sold" in result.reason


def test_price_collapse_cancels(clock: FixedClock) -> None:
    validator = _validator(_cache(metrics(price=Decimal("0.5"))), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "price dropped" in result.reason


def test_liquidity_collapse_cancels(clock: FixedClock) -> None:
    validator = _validator(_cache(metrics(liquidity=Decimal("100"))), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "liquidity dropped" in result.reason


def test_excess_slippage_cancels(clock: FixedClock) -> None:
    validator = _validator(_cache(metrics(slippage_bps=Decimal("500"))), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "slippage" in result.reason


def test_dev_sold_cancels(clock: FixedClock) -> None:
    validator = _validator(_cache(metrics(dev_sold=True)), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "dev sold" in result.reason


def test_sell_pressure_cancels(clock: FixedClock) -> None:
    fresh = metrics(buy_volume=Decimal("10"), sell_volume=Decimal("100"))
    validator = _validator(_cache(fresh), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "sell pressure" in result.reason


def test_smart_wallet_exit_cancels(clock: FixedClock) -> None:
    validator = _validator(_cache(metrics(smart_wallet_addresses=(WALLET_B,))), clock)
    decision_candidate = candidate(
        current=snapshot(token_metrics=metrics(smart_wallet_addresses=(WALLET_A, WALLET_B)))
    )
    result = validator.validate(decision_candidate, _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "smart wallet" in result.reason


def test_lp_supply_change_cancels(clock: FixedClock) -> None:
    fresh = metrics(lp_state=LpState(lp_token_supply=Decimal("400")))
    validator = _validator(_cache(fresh), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "LP token supply changed" in result.reason


def test_unchanged_state_passes(clock: FixedClock) -> None:
    validator = _validator(_cache(metrics()), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.PASS
    assert result.passed
    assert result.checked_snapshot is not None


@pytest.mark.parametrize("zero_field", ["price", "liquidity"])
def test_non_positive_baseline_cancels(clock: FixedClock, zero_field: str) -> None:
    validator = _validator(_cache(metrics()), clock)
    baseline = candidate(current=snapshot(token_metrics=metrics(**{zero_field: Decimal("0")})))
    result = validator.validate(baseline, _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "undefined" in result.reason
