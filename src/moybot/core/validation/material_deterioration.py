"""Material-deterioration check (PROJECT_SPEC.md §5).

The validator re-captures state immediately before acting and compares it with the state the
decision was made on. It cancels when:

* the required policies are not configured;
* no fresh snapshot can be captured;
* the fresh snapshot is older or further behind than the configured staleness policy allows;
* any volatile field the check depends on is unknown, in either snapshot;
* or a configured deterioration limit is breached.

Every limit comes from configuration. PROJECT_SPEC.md §9 leaves risk percentages and criteria
open, so an unconfigured validator cancels everything instead of inventing a limit. That is the
fail-closed behaviour §5 and §10.8 require.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import final

from moybot.core.clock import Clock
from moybot.core.model.candidate import Candidate
from moybot.core.model.decision import Decision, ValidationOutcome, ValidationResult
from moybot.core.model.primitives import Pubkey, Slot
from moybot.core.model.snapshot import Snapshot
from moybot.core.snapshots.builder import SnapshotBuilder

__all__ = [
    "DeteriorationPolicy",
    "MaterialDeteriorationValidator",
    "StalenessPolicy",
]


@final
@dataclass(frozen=True, slots=True)
class StalenessPolicy:
    """How old and how far behind a snapshot may be at execution time.

    Both limits must be supplied; there is no default, because the latency target and acceptable
    staleness are OPEN QUESTIONS (PROJECT_SPEC.md §9).
    """

    max_snapshot_age_ms: int
    max_slot_lag: int


@final
@dataclass(frozen=True, slots=True)
class DeteriorationPolicy:
    """Limits describing what counts as material deterioration (PROJECT_SPEC.md §5).

    Fractions are expressed as a share of the value observed at decision time, e.g. a
    ``max_price_drop_fraction`` of ``0.1`` cancels on a drop of more than 10%. The values
    themselves are configuration, never defaults.
    """

    max_price_drop_fraction: Decimal
    max_liquidity_drop_fraction: Decimal
    max_slippage_bps: Decimal
    max_sell_pressure_ratio: Decimal
    cancel_on_dev_sold: bool
    cancel_on_smart_wallet_exit: bool
    cancel_on_lp_supply_change: bool


@final
@dataclass(frozen=True, slots=True)
class _VolatileView:
    """The volatile fields of PROJECT_SPEC.md §5, all known."""

    price: Decimal
    liquidity: Decimal
    slippage_bps: Decimal
    dev_sold: bool
    buy_volume: Decimal
    sell_volume: Decimal
    smart_wallets: frozenset[Pubkey]
    lp_token_supply: Decimal | None


def _cancel(reason: str, snapshot: Snapshot | None = None) -> ValidationResult:
    return ValidationResult(
        outcome=ValidationOutcome.CANCELLED, reason=reason, checked_snapshot=snapshot
    )


def _read_volatile(snapshot: Snapshot) -> _VolatileView | tuple[str, ...]:
    """Read the volatile fields, or return the names of those that are unknown.

    Unknown is never coerced to zero: an unknown volatile field is a reason to cancel.
    """
    metrics = snapshot.metrics
    price = metrics.price
    liquidity = metrics.liquidity
    slippage_bps = metrics.slippage_bps
    dev_sold = metrics.dev_sold
    buy_volume = metrics.buy_volume
    sell_volume = metrics.sell_volume
    unknown: list[str] = []
    if price is None:
        unknown.append("price")
    if liquidity is None:
        unknown.append("liquidity")
    if slippage_bps is None:
        unknown.append("slippage_bps")
    if dev_sold is None:
        unknown.append("dev_sold")
    if buy_volume is None:
        unknown.append("buy_volume")
    if sell_volume is None:
        unknown.append("sell_volume")
    if (
        price is None
        or liquidity is None
        or slippage_bps is None
        or dev_sold is None
        or buy_volume is None
        or sell_volume is None
    ):
        return tuple(unknown)
    return _VolatileView(
        price=price,
        liquidity=liquidity,
        slippage_bps=slippage_bps,
        dev_sold=dev_sold,
        buy_volume=buy_volume,
        sell_volume=sell_volume,
        smart_wallets=frozenset(metrics.smart_wallet_addresses),
        lp_token_supply=metrics.lp_state.lp_token_supply,
    )


def _drop_fraction(before: Decimal, after: Decimal) -> Decimal | None:
    """Fractional decrease from ``before`` to ``after``; ``None`` when undefined."""
    if before <= 0:
        return None
    return (before - after) / before


@final
class MaterialDeteriorationValidator:
    """Fresh-state re-check immediately before an action."""

    def __init__(
        self,
        builder: SnapshotBuilder,
        clock: Clock,
        staleness_policy: StalenessPolicy | None = None,
        deterioration_policy: DeteriorationPolicy | None = None,
    ) -> None:
        self._builder = builder
        self._clock = clock
        self._staleness_policy = staleness_policy
        self._deterioration_policy = deterioration_policy

    @property
    def is_configured(self) -> bool:
        return self._staleness_policy is not None and self._deterioration_policy is not None

    def validate(
        self, candidate: Candidate, decision: Decision, current_slot: Slot
    ) -> ValidationResult:
        del decision
        staleness = self._staleness_policy
        deterioration = self._deterioration_policy
        if staleness is None:
            return _cancel(
                "staleness policy not configured; acceptable staleness is an OPEN QUESTION "
                "(PROJECT_SPEC.md §9), so validation fails closed"
            )
        if deterioration is None:
            return _cancel(
                "deterioration policy not configured; material-deterioration limits are an "
                "OPEN QUESTION (PROJECT_SPEC.md §9), so validation fails closed"
            )

        fresh = self._builder.capture(candidate.mint)
        if fresh is None:
            return _cancel("no fresh snapshot available for the token at validation time")

        age_ms = fresh.age_ms(self._clock.now_ms())
        if age_ms > staleness.max_snapshot_age_ms:
            return _cancel(
                f"fresh snapshot is {age_ms} ms old, limit is {staleness.max_snapshot_age_ms} ms",
                fresh,
            )
        slot_lag = fresh.slot_lag(current_slot)
        if slot_lag > staleness.max_slot_lag:
            return _cancel(
                f"fresh snapshot is {slot_lag} slots behind slot {current_slot}, limit is "
                f"{staleness.max_slot_lag}",
                fresh,
            )

        before = _read_volatile(candidate.snapshot)
        if isinstance(before, tuple):
            return _cancel(
                f"volatile fields unknown in the decision snapshot: {', '.join(before)}", fresh
            )
        after = _read_volatile(fresh)
        if isinstance(after, tuple):
            return _cancel(f"volatile fields unknown at validation time: {', '.join(after)}", fresh)

        return self._compare(before, after, fresh, deterioration)

    def _compare(
        self,
        before: _VolatileView,
        after: _VolatileView,
        fresh: Snapshot,
        policy: DeteriorationPolicy,
    ) -> ValidationResult:
        price_drop = _drop_fraction(before.price, after.price)
        if price_drop is None:
            return _cancel("price at decision time was not positive; drop is undefined", fresh)
        if price_drop > policy.max_price_drop_fraction:
            return _cancel(
                f"price dropped by {price_drop}, limit is {policy.max_price_drop_fraction}",
                fresh,
            )

        liquidity_drop = _drop_fraction(before.liquidity, after.liquidity)
        if liquidity_drop is None:
            return _cancel("liquidity at decision time was not positive; drop is undefined", fresh)
        if liquidity_drop > policy.max_liquidity_drop_fraction:
            return _cancel(
                f"liquidity dropped by {liquidity_drop}, limit is "
                f"{policy.max_liquidity_drop_fraction}",
                fresh,
            )

        if after.slippage_bps > policy.max_slippage_bps:
            return _cancel(
                f"slippage {after.slippage_bps} bps exceeds limit {policy.max_slippage_bps} bps",
                fresh,
            )

        if policy.cancel_on_dev_sold and after.dev_sold:
            return _cancel("dev sold as of the fresh snapshot", fresh)

        if after.buy_volume <= 0:
            return _cancel("buy volume is not positive; sell pressure is undefined", fresh)
        sell_pressure = after.sell_volume / after.buy_volume
        if sell_pressure > policy.max_sell_pressure_ratio:
            return _cancel(
                f"sell pressure {sell_pressure} exceeds limit {policy.max_sell_pressure_ratio}",
                fresh,
            )

        if policy.cancel_on_smart_wallet_exit:
            exited = before.smart_wallets - after.smart_wallets
            if exited:
                return _cancel(
                    f"{len(exited)} smart wallet(s) no longer present since the decision snapshot",
                    fresh,
                )

        if policy.cancel_on_lp_supply_change and before.lp_token_supply != after.lp_token_supply:
            return _cancel(
                "LP token supply changed between the decision snapshot and validation", fresh
            )

        return ValidationResult(
            outcome=ValidationOutcome.PASS,
            reason="no material deterioration detected against fresh state",
            checked_snapshot=fresh,
        )
