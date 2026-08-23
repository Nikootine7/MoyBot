"""Material-deterioration check (PROJECT_SPEC.md §5).

Immediately before acting, the validator re-reads the token's state through the fresh-state port
and compares it with the state the decision was made on. Re-reading is mandatory: comparing the
decision snapshot with itself would conclude that nothing changed, which is the one answer this
gate must never give by construction (docs/DECISIONS.md D-011).

It cancels when:

* the required policies are not configured, or no refresher is configured;
* the refresh is unavailable;
* the refreshed state is older or further behind than the configured staleness policy allows;
* any volatile field the check depends on is unknown, in either state;
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
from moybot.core.ingestion.refresh_port import RefreshedState, StateRefresher
from moybot.core.model.candidate import Candidate
from moybot.core.model.decision import (
    Decision,
    RefreshAudit,
    StalenessAudit,
    ValidationOutcome,
    ValidationResult,
    VolatileComparison,
)
from moybot.core.model.primitives import Pubkey, Slot
from moybot.core.model.snapshot import Snapshot
from moybot.core.snapshots.builder import SnapshotBuilder
from moybot.core.state.cache_port import ContinuousStateCache

__all__ = [
    "DeteriorationPolicy",
    "MaterialDeteriorationValidator",
    "StalenessPolicy",
]


@final
@dataclass(frozen=True, slots=True)
class StalenessPolicy:
    """How old and how far behind refreshed state may be at execution time.

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


def _comparisons(before: _VolatileView, after: _VolatileView) -> tuple[VolatileComparison, ...]:
    """Record every volatile value the check looked at, on both sides."""
    return (
        VolatileComparison("price", str(before.price), str(after.price)),
        VolatileComparison("liquidity", str(before.liquidity), str(after.liquidity)),
        VolatileComparison("slippage_bps", str(before.slippage_bps), str(after.slippage_bps)),
        VolatileComparison("dev_sold", str(before.dev_sold), str(after.dev_sold)),
        VolatileComparison("buy_volume", str(before.buy_volume), str(after.buy_volume)),
        VolatileComparison("sell_volume", str(before.sell_volume), str(after.sell_volume)),
        VolatileComparison(
            "smart_wallet_count", str(len(before.smart_wallets)), str(len(after.smart_wallets))
        ),
        VolatileComparison(
            "lp_token_supply", str(before.lp_token_supply), str(after.lp_token_supply)
        ),
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
        cache: ContinuousStateCache,
        clock: Clock,
        refresher: StateRefresher | None = None,
        staleness_policy: StalenessPolicy | None = None,
        deterioration_policy: DeteriorationPolicy | None = None,
    ) -> None:
        self._builder = builder
        self._cache = cache
        self._clock = clock
        self._refresher = refresher
        self._staleness_policy = staleness_policy
        self._deterioration_policy = deterioration_policy

    @property
    def is_configured(self) -> bool:
        return (
            self._refresher is not None
            and self._staleness_policy is not None
            and self._deterioration_policy is not None
        )

    def validate(
        self, candidate: Candidate, decision: Decision, current_slot: Slot
    ) -> ValidationResult:
        del decision
        staleness = self._staleness_policy
        deterioration = self._deterioration_policy
        refresher = self._refresher
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
        if refresher is None:
            return _cancel(
                "no state refresher configured; fresh state cannot be read, so validation "
                "fails closed (docs/DECISIONS.md D-011)"
            )

        refreshed = refresher.refresh(candidate.mint)
        if not isinstance(refreshed, RefreshedState):
            return _cancel(
                f"fresh state unavailable: {refreshed.reason}",
                refresh=RefreshAudit(
                    refresher=refresher.name,
                    available=False,
                    unavailable_reason=refreshed.reason,
                ),
            )
        audit = RefreshAudit(
            refresher=refresher.name,
            available=True,
            slot=refreshed.slot,
            observed_at_ms=refreshed.observed_at_ms,
        )

        fresh = self._apply(refreshed)
        if fresh is None:
            return _cancel("refreshed state could not be captured as a snapshot", refresh=audit)

        # The refreshed read may be ahead of the slot the event arrived on; the check is against
        # the most recent slot either of them has seen.
        checked_slot = Slot(max(int(current_slot), int(refreshed.slot)))
        checked_at_ms = self._clock.now_ms()
        measured = StalenessAudit(
            checked_at_ms=checked_at_ms,
            age_ms=fresh.age_ms(checked_at_ms),
            current_slot=checked_slot,
            slot_lag=fresh.slot_lag(checked_slot),
        )
        if measured.age_ms > staleness.max_snapshot_age_ms:
            return _cancel(
                f"refreshed state is {measured.age_ms} ms old, limit is "
                f"{staleness.max_snapshot_age_ms} ms",
                snapshot=fresh,
                refresh=audit,
                staleness=measured,
                limit="max_snapshot_age_ms",
            )
        if measured.slot_lag > staleness.max_slot_lag:
            return _cancel(
                f"refreshed state is {measured.slot_lag} slots behind slot {checked_slot}, "
                f"limit is {staleness.max_slot_lag}",
                snapshot=fresh,
                refresh=audit,
                staleness=measured,
                limit="max_slot_lag",
            )

        before = _read_volatile(candidate.snapshot)
        if isinstance(before, tuple):
            return _cancel(
                f"volatile fields unknown in the decision snapshot: {', '.join(before)}",
                snapshot=fresh,
                refresh=audit,
                staleness=measured,
            )
        after = _read_volatile(fresh)
        if isinstance(after, tuple):
            return _cancel(
                f"volatile fields unknown at validation time: {', '.join(after)}",
                snapshot=fresh,
                refresh=audit,
                staleness=measured,
            )

        return _compare(before, after, fresh, deterioration, audit, measured)

    def _apply(self, refreshed: RefreshedState) -> Snapshot | None:
        """Write the refreshed read into continuous state and capture it as a snapshot.

        The refreshed read is state, not an observation: it updates the cache so the snapshot is
        a complete picture, but it never becomes an event, a delta, or a scored input.
        """
        self._cache.apply(refreshed.to_patch())
        return self._builder.capture(refreshed.mint)


def _cancel(
    reason: str,
    snapshot: Snapshot | None = None,
    refresh: RefreshAudit | None = None,
    staleness: StalenessAudit | None = None,
    comparisons: tuple[VolatileComparison, ...] = (),
    limit: str | None = None,
) -> ValidationResult:
    return ValidationResult(
        outcome=ValidationOutcome.CANCELLED,
        reason=reason,
        checked_snapshot=snapshot,
        refresh=refresh,
        staleness=staleness,
        comparisons=comparisons,
        breached_limit=limit,
    )


def _compare(
    before: _VolatileView,
    after: _VolatileView,
    fresh: Snapshot,
    policy: DeteriorationPolicy,
    refresh: RefreshAudit,
    staleness: StalenessAudit,
) -> ValidationResult:
    compared = _comparisons(before, after)

    def cancel(reason: str, limit: str | None = None) -> ValidationResult:
        return _cancel(
            reason,
            snapshot=fresh,
            refresh=refresh,
            staleness=staleness,
            comparisons=compared,
            limit=limit,
        )

    price_drop = _drop_fraction(before.price, after.price)
    if price_drop is None:
        return cancel("price at decision time was not positive; drop is undefined")
    if price_drop > policy.max_price_drop_fraction:
        return cancel(
            f"price dropped by {price_drop}, limit is {policy.max_price_drop_fraction}",
            "max_price_drop_fraction",
        )

    liquidity_drop = _drop_fraction(before.liquidity, after.liquidity)
    if liquidity_drop is None:
        return cancel("liquidity at decision time was not positive; drop is undefined")
    if liquidity_drop > policy.max_liquidity_drop_fraction:
        return cancel(
            f"liquidity dropped by {liquidity_drop}, limit is {policy.max_liquidity_drop_fraction}",
            "max_liquidity_drop_fraction",
        )

    if after.slippage_bps > policy.max_slippage_bps:
        return cancel(
            f"slippage {after.slippage_bps} bps exceeds limit {policy.max_slippage_bps} bps",
            "max_slippage_bps",
        )

    if policy.cancel_on_dev_sold and after.dev_sold:
        return cancel("dev sold as of the refreshed state", "cancel_on_dev_sold")

    if after.buy_volume <= 0:
        return cancel("buy volume is not positive; sell pressure is undefined")
    sell_pressure = after.sell_volume / after.buy_volume
    if sell_pressure > policy.max_sell_pressure_ratio:
        return cancel(
            f"sell pressure {sell_pressure} exceeds limit {policy.max_sell_pressure_ratio}",
            "max_sell_pressure_ratio",
        )

    if policy.cancel_on_smart_wallet_exit:
        exited = before.smart_wallets - after.smart_wallets
        if exited:
            return cancel(
                f"{len(exited)} smart wallet(s) no longer present since the decision snapshot",
                "cancel_on_smart_wallet_exit",
            )

    if policy.cancel_on_lp_supply_change and before.lp_token_supply != after.lp_token_supply:
        return cancel(
            "LP token supply changed between the decision snapshot and validation",
            "cancel_on_lp_supply_change",
        )

    return ValidationResult(
        outcome=ValidationOutcome.PASS,
        reason="no material deterioration detected against refreshed state",
        checked_snapshot=fresh,
        refresh=refresh,
        staleness=staleness,
        comparisons=compared,
    )
