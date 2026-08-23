"""Replay fixture format.

STATUS: EXPERIMENTAL, Phase 1/2 artifact. Schema version 2 (docs/DECISIONS.md D-010).

This schema exists so the pipeline can run deterministically offline. It is explicitly **not** a
provider contract and implies nothing about which data provider MOYBOT will use, or about how a
live implementation would read fresh state: both remain OPEN QUESTIONS (PROJECT_SPEC.md §3, §9).

Only metric fields present in an update are applied to the cache, so a fixture can express
"this field was not reported" as distinct from "this field is zero". Events are listed
explicitly: the replay source never derives an event from the metrics.

Version 2 adds an optional ``validation_state`` block per observation: the state a re-read at
validation time would return (PROJECT_SPEC.md §5). It is not an observation, so it never enters
the delta, never produces an event, and is never scored.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import final

from pydantic import BaseModel, ConfigDict, Field

from moybot.core.ingestion.refresh_port import RefreshedState
from moybot.core.model.event import Event, parse_event_kind
from moybot.core.model.metrics import HolderDistribution, LpState, MetricFields, TokenState
from moybot.core.model.primitives import Pubkey, Slot, TimestampMs, parse_pubkey
from moybot.core.model.update import MarketUpdate

__all__ = ["FixtureFile", "ReplayEntry", "load_fixture"]

_SUPPORTED_SCHEMA_VERSION = 2


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TokenStateFixture(_StrictModel):
    """Observed mint-account state."""

    mint_authority: str | None = None
    freeze_authority: str | None = None
    update_authority: str | None = None
    supply: Decimal | None = None
    decimals: int | None = None

    def to_domain(self) -> TokenState:
        return TokenState(
            mint_authority=parse_pubkey(self.mint_authority) if self.mint_authority else None,
            freeze_authority=(
                parse_pubkey(self.freeze_authority) if self.freeze_authority else None
            ),
            update_authority=(
                parse_pubkey(self.update_authority) if self.update_authority else None
            ),
            supply=self.supply,
            decimals=self.decimals,
        )


class LpStateFixture(_StrictModel):
    """Observed liquidity-pool state."""

    pool: str | None = None
    base_reserve: Decimal | None = None
    quote_reserve: Decimal | None = None
    lp_token_supply: Decimal | None = None
    lp_tokens_burned: Decimal | None = None

    def to_domain(self) -> LpState:
        return LpState(
            pool=parse_pubkey(self.pool) if self.pool else None,
            base_reserve=self.base_reserve,
            quote_reserve=self.quote_reserve,
            lp_token_supply=self.lp_token_supply,
            lp_tokens_burned=self.lp_tokens_burned,
        )


class HoldersFixture(_StrictModel):
    """Observed holder distribution."""

    holder_count: int | None = None
    top_holder_shares: tuple[Decimal, ...] = ()

    def to_domain(self) -> HolderDistribution:
        return HolderDistribution(
            holder_count=self.holder_count, top_holder_shares=self.top_holder_shares
        )


class MetricsFixture(_StrictModel):
    """Partial metrics as reported by the source."""

    price: Decimal | None = None
    price_change: Decimal | None = None
    volume: Decimal | None = None
    buy_volume: Decimal | None = None
    sell_volume: Decimal | None = None
    liquidity: Decimal | None = None
    slippage_bps: Decimal | None = None
    holders: HoldersFixture | None = None
    dev_transaction_count: int | None = None
    dev_sold: bool | None = None
    smart_wallet_transaction_count: int | None = None
    smart_wallet_addresses: tuple[str, ...] | None = None
    wallet_cluster_ids: tuple[str, ...] | None = None
    token_state: TokenStateFixture | None = None
    lp_state: LpStateFixture | None = None

    def to_patch_fields(self) -> MetricFields:
        """Return only the metric fields this update explicitly reported.

        The mapping is written out field by field so that adding a metric to the domain model is
        a deliberate act rather than something a fixture can imply.
        """
        reported = self.model_fields_set
        candidates: MetricFields = (
            ("price", self.price),
            ("price_change", self.price_change),
            ("volume", self.volume),
            ("buy_volume", self.buy_volume),
            ("sell_volume", self.sell_volume),
            ("liquidity", self.liquidity),
            ("slippage_bps", self.slippage_bps),
            ("holders", self.holders.to_domain() if self.holders is not None else None),
            ("dev_transaction_count", self.dev_transaction_count),
            ("dev_sold", self.dev_sold),
            ("smart_wallet_transaction_count", self.smart_wallet_transaction_count),
            (
                "smart_wallet_addresses",
                tuple(parse_pubkey(item) for item in self.smart_wallet_addresses)
                if self.smart_wallet_addresses is not None
                else None,
            ),
            ("wallet_cluster_ids", self.wallet_cluster_ids),
            ("token_state", self.token_state.to_domain() if self.token_state is not None else None),
            ("lp_state", self.lp_state.to_domain() if self.lp_state is not None else None),
        )
        container_fields = frozenset(
            {
                "holders",
                "smart_wallet_addresses",
                "wallet_cluster_ids",
                "token_state",
                "lp_state",
            }
        )
        return tuple(
            (name, value)
            for name, value in candidates
            if name in reported and not (name in container_fields and value is None)
        )


class EventFixture(_StrictModel):
    """An event explicitly declared by the source."""

    kind: str
    payload: dict[str, str] = Field(default_factory=dict)

    def to_domain(self, mint: Pubkey, slot: Slot, timestamp_ms: TimestampMs, source: str) -> Event:
        return Event(
            kind=parse_event_kind(self.kind),
            mint=mint,
            slot=slot,
            timestamp_ms=timestamp_ms,
            source=source,
            payload=tuple(sorted(self.payload.items())),
        )


class ValidationStateFixture(_StrictModel):
    """State a re-read at validation time would return (docs/DECISIONS.md D-010, D-011).

    This models the answer to a fresh read, not a further observation from the stream. Declaring
    it is how an offline scenario can distinguish "nothing changed between the decision and the
    action" from "the token deteriorated in between", which PROJECT_SPEC.md §5 exists to catch.
    """

    slot: int
    observed_at_ms: int
    metrics: MetricsFixture = Field(default_factory=MetricsFixture)

    def to_domain(self, mint: Pubkey) -> RefreshedState:
        return RefreshedState(
            mint=mint,
            slot=Slot(self.slot),
            observed_at_ms=TimestampMs(self.observed_at_ms),
            fields=self.metrics.to_patch_fields(),
        )


class UpdateFixture(_StrictModel):
    """One observation of one token, with the fresh state a validation read would return."""

    mint: str
    slot: int
    observed_at_ms: int
    metrics: MetricsFixture = Field(default_factory=MetricsFixture)
    events: tuple[EventFixture, ...] = ()
    validation_state: ValidationStateFixture | None = None

    def to_domain(self, source: str, sequence: int) -> MarketUpdate:
        mint = parse_pubkey(self.mint)
        slot = Slot(self.slot)
        observed_at_ms = TimestampMs(self.observed_at_ms)
        return MarketUpdate(
            mint=mint,
            slot=slot,
            observed_at_ms=observed_at_ms,
            source=source,
            sequence=sequence,
            metrics=self.metrics.to_patch_fields(),
            declared_events=tuple(
                event.to_domain(mint, slot, observed_at_ms, source) for event in self.events
            ),
        )


@final
@dataclass(frozen=True, slots=True)
class ReplayEntry:
    """One replayed observation together with the fresh state declared alongside it."""

    update: MarketUpdate
    validation_state: RefreshedState | None = None


@final
class FixtureFile(_StrictModel):
    """A replay scenario."""

    schema_version: int
    name: str
    description: str = ""
    updates: tuple[UpdateFixture, ...] = ()

    def to_entries(self) -> tuple[ReplayEntry, ...]:
        """Convert the scenario into replay entries, numbered in file order."""
        source = f"replay:{self.name}"
        entries: list[ReplayEntry] = []
        for sequence, update in enumerate(self.updates):
            domain = update.to_domain(source, sequence)
            declared = update.validation_state
            entries.append(
                ReplayEntry(
                    update=domain,
                    validation_state=(
                        declared.to_domain(domain.mint) if declared is not None else None
                    ),
                )
            )
        return tuple(entries)

    def to_updates(self) -> tuple[MarketUpdate, ...]:
        """Convert the scenario into domain updates, numbered in file order."""
        return tuple(entry.update for entry in self.to_entries())


def load_fixture(path: Path) -> FixtureFile:
    """Load and validate a replay fixture."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    fixture = FixtureFile.model_validate(raw)
    if fixture.schema_version != _SUPPORTED_SCHEMA_VERSION:
        msg = (
            f"unsupported fixture schema_version {fixture.schema_version}; "
            f"expected {_SUPPORTED_SCHEMA_VERSION}"
        )
        raise ValueError(msg)
    return fixture
