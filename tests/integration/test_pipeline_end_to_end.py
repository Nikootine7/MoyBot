"""Deterministic end-to-end pipeline runs over replay fixtures.

Every threshold and limit used here is supplied by the test. The shipped configuration supplies
none, which is why the default-configuration test below expects no alert at all.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from moybot.adapters.replay.source import ReplayDataSource
from moybot.app.composition import build_pipeline
from moybot.app.config import AppConfig
from moybot.core.action.log_sink import CollectingAlertSink
from moybot.core.analysis.registry import HeavyAnalysisRegistry
from moybot.core.clock import FixedClock
from moybot.core.delta.differ import SnapshotDiffer
from moybot.core.events.registry import DeclaredEventDetector, EventDetectorRegistry
from moybot.core.filtering.accept_all import AcceptAllFilter
from moybot.core.filtering.chain import FilterChain
from moybot.core.model.decision import DecisionOutcome
from moybot.core.model.primitives import TimestampMs
from moybot.core.pipeline.runner import PipelineRunner, UpdateResult
from moybot.core.pipeline.stage import StageName
from moybot.core.snapshots.builder import SnapshotBuilder
from moybot.core.snapshots.file_store import InMemoryProvenanceStore, InMemorySnapshotStore
from moybot.core.state.memory_cache import InMemoryStateCache
from moybot.core.strategy.strategy_port import Strategy
from moybot.core.validation.material_deterioration import (
    DeteriorationPolicy,
    MaterialDeteriorationValidator,
    StalenessPolicy,
)
from tests.support import RejectingFilter, StubStrategy

_START_MS = TimestampMs(1_750_000_000_000)
_STALENESS = StalenessPolicy(max_snapshot_age_ms=60_000, max_slot_lag=10)
_DETERIORATION = DeteriorationPolicy(
    max_price_drop_fraction=Decimal("0.1"),
    max_liquidity_drop_fraction=Decimal("0.1"),
    max_slippage_bps=Decimal("100"),
    max_sell_pressure_ratio=Decimal("2"),
    cancel_on_dev_sold=True,
    cancel_on_smart_wallet_exit=False,
    cancel_on_lp_supply_change=False,
)


class _Harness:
    """A pipeline wired for tests, with in-memory stores."""

    def __init__(self, strategies: Sequence[Strategy], configure_validator: bool = True) -> None:
        self.clock = FixedClock(_START_MS)
        self.cache = InMemoryStateCache()
        self.snapshots = InMemorySnapshotStore()
        self.provenance = InMemoryProvenanceStore()
        self.sink = CollectingAlertSink()
        builder = SnapshotBuilder(self.cache)
        self.runner = PipelineRunner(
            cache=self.cache,
            detectors=EventDetectorRegistry([DeclaredEventDetector()]),
            snapshot_builder=builder,
            snapshot_store=self.snapshots,
            differ=SnapshotDiffer(),
            heavy_analysis=HeavyAnalysisRegistry([]),
            strategies=strategies,
            validator=MaterialDeteriorationValidator(
                builder=builder,
                clock=self.clock,
                staleness_policy=_STALENESS if configure_validator else None,
                deterioration_policy=_DETERIORATION if configure_validator else None,
            ),
            action_sink=self.sink,
            provenance_store=self.provenance,
            clock=self.clock,
        )

    def run(self, fixture: Path) -> tuple[UpdateResult, ...]:
        source = ReplayDataSource.from_file(fixture)
        return asyncio.run(self.runner.run_source(source))


def _stages(harness: _Harness) -> list[StageName]:
    return [record.stage for record in harness.provenance.records]


def test_update_without_event_does_no_further_work(fixture_dir: Path) -> None:
    harness = _Harness([StubStrategy("stub", DecisionOutcome.ADVANCE)])
    results = harness.run(fixture_dir / "no_event.json")
    assert [len(result.events) for result in results] == [0]
    assert harness.provenance.records == []
    assert harness.snapshots.appended == []
    assert harness.cache.tracked_mints() != ()


def test_event_reaches_an_alert(fixture_dir: Path) -> None:
    strategy = StubStrategy("stub", DecisionOutcome.ADVANCE, FilterChain([AcceptAllFilter()]))
    harness = _Harness([strategy])
    results = harness.run(fixture_dir / "smart_wallet_buy.json")
    assert [len(result.events) for result in results] == [0, 1]
    assert len(harness.sink.alerts) == 1
    alert = harness.sink.alerts[0]
    assert alert.decision.strategy == "stub"
    assert alert.validation.passed
    assert _stages(harness) == [
        StageName.EVENT_TRIGGER,
        StageName.DELTA_ANALYSIS,
        StageName.CANDIDATE_FILTERING,
        StageName.HEAVY_ANALYSIS,
        StageName.SCORING,
        StageName.PRE_TRADE_VALIDATION,
        StageName.ACTION,
    ]


def test_delta_reports_only_changed_fields(fixture_dir: Path) -> None:
    harness = _Harness([StubStrategy("stub", DecisionOutcome.REJECT)])
    harness.run(fixture_dir / "smart_wallet_buy.json")
    delta_record = next(
        record for record in harness.provenance.records if record.stage is StageName.DELTA_ANALYSIS
    )
    changed = delta_record.detail["changed_paths"]
    assert isinstance(changed, list)
    assert "price" in changed
    assert "dev_sold" not in changed


def test_filtered_out_candidate_stops_before_analysis(fixture_dir: Path) -> None:
    strategy = StubStrategy("stub", DecisionOutcome.ADVANCE, FilterChain([RejectingFilter()]))
    harness = _Harness([strategy])
    harness.run(fixture_dir / "smart_wallet_buy.json")
    assert strategy.evaluated == []
    assert harness.sink.alerts == []
    assert _stages(harness) == [
        StageName.EVENT_TRIGGER,
        StageName.DELTA_ANALYSIS,
        StageName.CANDIDATE_FILTERING,
    ]


def test_validation_cancels_on_unknown_volatile_field(fixture_dir: Path) -> None:
    harness = _Harness([StubStrategy("stub", DecisionOutcome.ADVANCE)])
    harness.run(fixture_dir / "unknown_volatile_field.json")
    assert harness.sink.alerts == []
    validation = next(
        record
        for record in harness.provenance.records
        if record.stage is StageName.PRE_TRADE_VALIDATION
    )
    assert validation.outcome == "cancelled"
    assert "slippage_bps" in str(validation.detail["reason"])


def test_unconfigured_validator_cancels_every_candidate(fixture_dir: Path) -> None:
    harness = _Harness([StubStrategy("stub", DecisionOutcome.ADVANCE)], configure_validator=False)
    harness.run(fixture_dir / "smart_wallet_buy.json")
    assert harness.sink.alerts == []


def test_not_configured_decision_never_reaches_validation(fixture_dir: Path) -> None:
    harness = _Harness([StubStrategy("stub", DecisionOutcome.NOT_CONFIGURED)])
    harness.run(fixture_dir / "smart_wallet_buy.json")
    assert harness.sink.alerts == []
    assert StageName.PRE_TRADE_VALIDATION not in _stages(harness)


def test_default_configuration_raises_no_alert(fixture_dir: Path, tmp_path: Path) -> None:
    sink = CollectingAlertSink()
    pipeline = build_pipeline(
        AppConfig(),
        clock=FixedClock(_START_MS),
        action_sink=sink,
        snapshot_store=InMemorySnapshotStore(),
        provenance_store=InMemoryProvenanceStore(),
        data_dir=tmp_path,
    )
    source = ReplayDataSource.from_file(fixture_dir / "smart_wallet_buy.json")
    results = asyncio.run(pipeline.runner.run_source(source))
    outcomes = {decision.outcome for result in results for decision in result.decisions}
    assert outcomes == {DecisionOutcome.NOT_CONFIGURED}
    assert sink.alerts == []
    assert [strategy.name for strategy in pipeline.strategies] == ["bot_a", "bot_b"]


def test_replay_is_deterministic(fixture_dir: Path) -> None:
    def record_ids() -> list[str]:
        harness = _Harness(
            [StubStrategy("stub", DecisionOutcome.ADVANCE, FilterChain([AcceptAllFilter()]))]
        )
        harness.run(fixture_dir / "smart_wallet_buy.json")
        return [record.record_id for record in harness.provenance.records]

    assert record_ids() == record_ids()
