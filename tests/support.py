"""Test-only doubles.

The numbers used here are test inputs, not domain decisions: nothing in this module is imported
by ``src/moybot``. Every threshold or weight a test needs is defined inside that test so it can
never leak into the shipped code (PROJECT_SPEC.md §10.3).
"""

from __future__ import annotations

from decimal import Decimal
from typing import final

from moybot.core.delta.differ import SnapshotDiffer
from moybot.core.filtering.chain import FilterChain
from moybot.core.model.candidate import Candidate, FilterVerdict
from moybot.core.model.decision import Decision, DecisionOutcome
from moybot.core.model.event import Event, parse_event_kind
from moybot.core.model.features import Feature, FeatureSet
from moybot.core.model.metrics import HolderDistribution, LpState, TokenMetrics, TokenState
from moybot.core.model.primitives import Pubkey, Slot, TimestampMs, parse_pubkey
from moybot.core.model.snapshot import Snapshot

MINT_A: Pubkey = parse_pubkey("MoyMintAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
MINT_B: Pubkey = parse_pubkey("MoyMintBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB")
WALLET_A: Pubkey = parse_pubkey("MoySmartWa" + "A" * 33)
WALLET_B: Pubkey = parse_pubkey("MoySmartWb" + "B" * 33)


def metrics(**overrides: object) -> TokenMetrics:
    """Build metrics with every volatile field known, then apply overrides."""
    base: dict[str, object] = {
        "price": Decimal("1"),
        "price_change": Decimal("0"),
        "volume": Decimal("100"),
        "buy_volume": Decimal("70"),
        "sell_volume": Decimal("30"),
        "liquidity": Decimal("1000"),
        "slippage_bps": Decimal("10"),
        "holders": HolderDistribution(holder_count=100, top_holder_shares=(Decimal("0.05"),)),
        "dev_transaction_count": 1,
        "dev_sold": False,
        "smart_wallet_transaction_count": 1,
        "smart_wallet_addresses": (WALLET_A,),
        "wallet_cluster_ids": (),
        "token_state": TokenState(supply=Decimal("1000000"), decimals=6),
        "lp_state": LpState(lp_token_supply=Decimal("500")),
    }
    base.update(overrides)
    return TokenMetrics(**base)  # type: ignore[arg-type]


def snapshot(
    mint: Pubkey = MINT_A,
    slot: int = 100,
    captured_at_ms: int = 1_750_000_000_000,
    sequence: int = 0,
    token_metrics: TokenMetrics | None = None,
) -> Snapshot:
    """Build a snapshot for tests."""
    return Snapshot(
        mint=mint,
        slot=Slot(slot),
        captured_at_ms=TimestampMs(captured_at_ms),
        sequence=sequence,
        metrics=token_metrics if token_metrics is not None else metrics(),
    )


def candidate(
    current: Snapshot | None = None,
    previous: Snapshot | None = None,
    event_kind: str = "test_event",
) -> Candidate:
    """Build a candidate for tests, with a delta derived from the two snapshots."""
    snap = current if current is not None else snapshot()
    return Candidate(
        mint=snap.mint,
        event=Event(
            kind=parse_event_kind(event_kind),
            mint=snap.mint,
            slot=snap.slot,
            timestamp_ms=snap.captured_at_ms,
            source="test",
        ),
        snapshot=snap,
        previous_snapshot=previous,
        delta=SnapshotDiffer().diff(previous, snap),
    )


@final
class RejectingFilter:
    """A filter that always rejects, for testing short-circuit behaviour."""

    def __init__(self, name: str = "rejecting") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def evaluate(self, candidate: Candidate) -> FilterVerdict:
        del candidate
        return FilterVerdict(filter_name=self._name, accepted=False, reason="test rejection")


@final
class RecordingFilter:
    """A filter that accepts and records how often it ran."""

    def __init__(self, name: str = "recording") -> None:
        self._name = name
        self.calls = 0

    @property
    def name(self) -> str:
        return self._name

    def evaluate(self, candidate: Candidate) -> FilterVerdict:
        del candidate
        self.calls += 1
        return FilterVerdict(filter_name=self._name, accepted=True)


@final
class StubStrategy:
    """A strategy with a caller-supplied outcome, so pipeline tests need no threshold."""

    def __init__(
        self,
        name: str,
        outcome: DecisionOutcome,
        filters: FilterChain | None = None,
    ) -> None:
        self._name = name
        self._outcome = outcome
        self._filters = filters if filters is not None else FilterChain([])
        self.evaluated: list[Candidate] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def filters(self) -> FilterChain:
        return self._filters

    def evaluate(self, candidate: Candidate, features: FeatureSet) -> Decision:
        del features
        self.evaluated.append(candidate)
        return Decision(
            strategy=self._name,
            mint=candidate.mint,
            outcome=self._outcome,
            reason="stubbed test outcome",
        )


@final
class StubAnalysisModule:
    """A heavy-analysis module that returns a fixed feature, for scoring tests."""

    def __init__(self, name: str, feature: str, value: Decimal) -> None:
        self._name = name
        self._feature = feature
        self._value = value

    @property
    def name(self) -> str:
        return self._name

    def analyze(self, candidate: Candidate) -> tuple[Feature, ...]:
        del candidate
        return (Feature(name=self._feature, value=self._value, produced_by=self._name),)


@final
class StubRejectionRule:
    """A hard rejection rule with a caller-supplied verdict."""

    def __init__(self, name: str, reason: str | None) -> None:
        self._name = name
        self._reason = reason

    @property
    def name(self) -> str:
        return self._name

    def rejects(self, candidate: Candidate, features: FeatureSet) -> str | None:
        del candidate, features
        return self._reason
