"""Final pre-trade validation.

The limits below are test inputs. The shipped validator has none and cancels everything until it
is configured (PROJECT_SPEC.md §5, §9, §10.8).

Every case supplies the state a validation-time read returns, because that read is what the check
compares the decision against (docs/DECISIONS.md D-011).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from moybot.core.clock import FixedClock
from moybot.core.ingestion.refresh_port import RefreshResult, RefreshUnavailable
from moybot.core.model.decision import Decision, DecisionOutcome, ValidationOutcome
from moybot.core.model.metrics import LpState, TokenMetrics
from moybot.core.model.primitives import Slot
from moybot.core.snapshots.builder import SnapshotBuilder
from moybot.core.state.memory_cache import InMemoryStateCache
from moybot.core.validation.material_deterioration import (
    DeteriorationPolicy,
    MaterialDeteriorationValidator,
    StalenessPolicy,
)
from tests.support import (
    MINT_A,
    WALLET_A,
    WALLET_B,
    StubRefresher,
    candidate,
    metrics,
    refreshed,
    snapshot,
)

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


def _validator(
    result: RefreshResult,
    clock: FixedClock,
    staleness: StalenessPolicy | None = _STALENESS,
    deterioration: DeteriorationPolicy | None = _DETERIORATION,
    refresher: StubRefresher | None = None,
) -> MaterialDeteriorationValidator:
    cache = InMemoryStateCache()
    return MaterialDeteriorationValidator(
        builder=SnapshotBuilder(cache),
        cache=cache,
        clock=clock,
        refresher=refresher if refresher is not None else StubRefresher(result),
        staleness_policy=staleness,
        deterioration_policy=deterioration,
    )


def _fresh(**overrides: object) -> RefreshResult:
    """The validation-time read returns the token unchanged, apart from ``overrides``."""
    return refreshed(metrics(**overrides))


def test_unconfigured_validator_cancels(clock: FixedClock) -> None:
    validator = _validator(_fresh(), clock, staleness=None, deterioration=None)
    assert not validator.is_configured
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "staleness policy not configured" in result.reason


def test_missing_deterioration_policy_cancels(clock: FixedClock) -> None:
    validator = _validator(_fresh(), clock, deterioration=None)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "deterioration policy not configured" in result.reason


def test_missing_refresher_cancels(clock: FixedClock) -> None:
    cache = InMemoryStateCache()
    validator = MaterialDeteriorationValidator(
        builder=SnapshotBuilder(cache),
        cache=cache,
        clock=clock,
        staleness_policy=_STALENESS,
        deterioration_policy=_DETERIORATION,
    )
    assert not validator.is_configured
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "no state refresher configured" in result.reason


def test_unavailable_refresh_cancels(clock: FixedClock) -> None:
    unavailable = RefreshUnavailable(mint=MINT_A, reason="provider did not answer")
    validator = _validator(unavailable, clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "fresh state unavailable: provider did not answer" in result.reason
    assert result.refresh is not None
    assert not result.refresh.available
    assert result.refresh.unavailable_reason == "provider did not answer"


def test_the_refreshed_state_is_read_for_the_candidate(clock: FixedClock) -> None:
    refresher = StubRefresher(_fresh())
    validator = _validator(_fresh(), clock, refresher=refresher)
    validator.validate(candidate(), _DECISION, Slot(100))
    assert refresher.calls == [MINT_A]


def test_stale_refresh_cancels_on_age(clock: FixedClock) -> None:
    validator = _validator(_fresh(), clock)
    clock.advance_ms(_STALENESS.max_snapshot_age_ms + 1)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert result.breached_limit == "max_snapshot_age_ms"
    assert result.staleness is not None
    assert result.staleness.age_ms == _STALENESS.max_snapshot_age_ms + 1


def test_stale_refresh_cancels_on_slot_lag(clock: FixedClock) -> None:
    validator = _validator(_fresh(), clock)
    result = validator.validate(candidate(), _DECISION, Slot(200))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert result.breached_limit == "max_slot_lag"
    assert result.staleness is not None
    assert result.staleness.slot_lag == 100


def test_unknown_volatile_field_in_decision_snapshot_cancels(clock: FixedClock) -> None:
    validator = _validator(_fresh(), clock)
    stale_candidate = candidate(current=snapshot(token_metrics=metrics(slippage_bps=None)))
    result = validator.validate(stale_candidate, _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "volatile fields unknown in the decision snapshot: slippage_bps" in result.reason


def test_unknown_volatile_field_at_validation_time_cancels(clock: FixedClock) -> None:
    validator = _validator(_fresh(dev_sold=None), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "volatile fields unknown at validation time: dev_sold" in result.reason


def test_price_collapse_cancels(clock: FixedClock) -> None:
    validator = _validator(_fresh(price=Decimal("0.5")), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "price dropped" in result.reason
    assert result.breached_limit == "max_price_drop_fraction"


def test_liquidity_collapse_cancels(clock: FixedClock) -> None:
    validator = _validator(_fresh(liquidity=Decimal("100")), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "liquidity dropped" in result.reason
    assert result.breached_limit == "max_liquidity_drop_fraction"


def test_excess_slippage_cancels(clock: FixedClock) -> None:
    validator = _validator(_fresh(slippage_bps=Decimal("500")), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "slippage" in result.reason
    assert result.breached_limit == "max_slippage_bps"


def test_dev_sold_cancels(clock: FixedClock) -> None:
    validator = _validator(_fresh(dev_sold=True), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "dev sold" in result.reason
    assert result.breached_limit == "cancel_on_dev_sold"


def test_sell_pressure_cancels(clock: FixedClock) -> None:
    validator = _validator(
        _fresh(buy_volume=Decimal("10"), sell_volume=Decimal("100")),
        clock,
    )
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "sell pressure" in result.reason
    assert result.breached_limit == "max_sell_pressure_ratio"


def test_smart_wallet_exit_cancels(clock: FixedClock) -> None:
    """Uses the wallets the source declared; it does not define what a smart wallet is."""
    validator = _validator(_fresh(smart_wallet_addresses=(WALLET_B,)), clock)
    decision_candidate = candidate(
        current=snapshot(token_metrics=metrics(smart_wallet_addresses=(WALLET_A, WALLET_B)))
    )
    result = validator.validate(decision_candidate, _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "smart wallet" in result.reason
    assert result.breached_limit == "cancel_on_smart_wallet_exit"


def test_lp_supply_change_cancels(clock: FixedClock) -> None:
    validator = _validator(_fresh(lp_state=LpState(lp_token_supply=Decimal("400"))), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "LP token supply changed" in result.reason
    assert result.breached_limit == "cancel_on_lp_supply_change"


def test_unchanged_state_passes(clock: FixedClock) -> None:
    validator = _validator(_fresh(), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.PASS
    assert result.passed
    assert result.checked_snapshot is not None
    assert result.breached_limit is None


def test_passing_result_records_what_was_checked(clock: FixedClock) -> None:
    """PROJECT_SPEC.md §4: the check must be reconstructible from what it reports."""
    validator = _validator(refreshed(metrics(), slot=101, observed_at_ms=1_750_000_000_000), clock)
    result = validator.validate(candidate(), _DECISION, Slot(100))
    assert result.refresh is not None
    assert result.refresh.available
    assert result.refresh.slot == Slot(101)
    assert result.staleness is not None
    assert result.staleness.age_ms == 0
    assert result.staleness.current_slot == Slot(101)
    assert result.staleness.slot_lag == 0
    compared = {comparison.field for comparison in result.comparisons}
    assert compared == {
        "price",
        "liquidity",
        "slippage_bps",
        "dev_sold",
        "buy_volume",
        "sell_volume",
        "smart_wallet_count",
        "lp_token_supply",
    }


def test_refresh_does_not_mutate_the_decision_snapshot(clock: FixedClock) -> None:
    validator = _validator(_fresh(price=Decimal("0.5")), clock)
    decided = candidate()
    before: TokenMetrics = decided.snapshot.metrics
    validator.validate(decided, _DECISION, Slot(100))
    assert decided.snapshot.metrics == before
    assert decided.snapshot.metrics.price == Decimal("1")


@pytest.mark.parametrize("zero_field", ["price", "liquidity"])
def test_non_positive_baseline_cancels(clock: FixedClock, zero_field: str) -> None:
    validator = _validator(_fresh(), clock)
    baseline = candidate(current=snapshot(token_metrics=metrics(**{zero_field: Decimal("0")})))
    result = validator.validate(baseline, _DECISION, Slot(100))
    assert result.outcome is ValidationOutcome.CANCELLED
    assert "undefined" in result.reason
