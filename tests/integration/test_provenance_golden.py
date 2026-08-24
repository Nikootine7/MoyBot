"""Golden-file test locking the provenance audit schema.

The point is not the exact numbers but the shape: PROJECT_SPEC.md §4 requires that a decision be
reconstructible from its record, so a change to these records must be a deliberate schema change.
Regenerate with ``python -m tests.golden.regenerate``.
"""

from __future__ import annotations

import asyncio
import json
from decimal import Decimal
from pathlib import Path

from moybot.adapters.replay.session import open_replay
from moybot.core.action.log_sink import CollectingAlertSink
from moybot.core.analysis.registry import HeavyAnalysisRegistry
from moybot.core.delta.differ import SnapshotDiffer
from moybot.core.events.registry import DeclaredEventDetector, EventDetectorRegistry
from moybot.core.filtering.accept_all import AcceptAllFilter
from moybot.core.filtering.chain import FilterChain
from moybot.core.model.decision import DecisionOutcome
from moybot.core.model.primitives import JsonValue
from moybot.core.pipeline.runner import PipelineRunner
from moybot.core.serialization import to_json_value
from moybot.core.snapshots.builder import SnapshotBuilder
from moybot.core.snapshots.file_store import InMemoryProvenanceStore, InMemorySnapshotStore
from moybot.core.state.memory_cache import InMemoryStateCache
from moybot.core.validation.material_deterioration import (
    DeteriorationPolicy,
    MaterialDeteriorationValidator,
    StalenessPolicy,
)
from tests.support import StubStrategy

STALENESS = StalenessPolicy(max_snapshot_age_ms=60_000, max_slot_lag=10)
DETERIORATION = DeteriorationPolicy(
    max_price_drop_fraction=Decimal("0.1"),
    max_liquidity_drop_fraction=Decimal("0.1"),
    max_slippage_bps=Decimal("100"),
    max_sell_pressure_ratio=Decimal("2"),
    cancel_on_dev_sold=True,
    cancel_on_smart_wallet_exit=False,
    cancel_on_lp_supply_change=False,
)
GOLDEN_NAME = "provenance_smart_wallet_buy.json"
SCENARIO_NAME = "smart_wallet_buy.json"


def run_scenario(fixture: Path) -> list[JsonValue]:
    """Replay a fixture and return its provenance records as JSON values."""
    session = open_replay(fixture)
    clock = session.clock
    cache = InMemoryStateCache()
    builder = SnapshotBuilder(cache)
    provenance = InMemoryProvenanceStore()
    runner = PipelineRunner(
        cache=cache,
        detectors=EventDetectorRegistry([DeclaredEventDetector()]),
        snapshot_builder=builder,
        snapshot_store=InMemorySnapshotStore(),
        differ=SnapshotDiffer(),
        heavy_analysis=HeavyAnalysisRegistry([]),
        strategies=[
            StubStrategy("stub", DecisionOutcome.ADVANCE, FilterChain([AcceptAllFilter()]))
        ],
        validator=MaterialDeteriorationValidator(
            builder=builder,
            cache=cache,
            clock=clock,
            refresher=session.refresher,
            staleness_policy=STALENESS,
            deterioration_policy=DETERIORATION,
        ),
        action_sink=CollectingAlertSink(),
        provenance_store=provenance,
        clock=clock,
    )
    asyncio.run(runner.run_source(session.source))
    return [to_json_value(record) for record in provenance.records]


def test_provenance_matches_the_golden_file(fixture_dir: Path, golden_dir: Path) -> None:
    actual = run_scenario(fixture_dir / SCENARIO_NAME)
    expected = json.loads((golden_dir / GOLDEN_NAME).read_text(encoding="utf-8"))
    assert actual == expected


def test_every_record_carries_full_context(fixture_dir: Path) -> None:
    for record in run_scenario(fixture_dir / SCENARIO_NAME):
        assert isinstance(record, dict)
        assert set(record) == {
            "record_id",
            "correlation_id",
            "stage",
            "mint",
            "occurred_at_ms",
            "slot",
            "outcome",
            "duration_us",
            "detail",
        }
        # Records are timestamped with the time the data was observed, not the time of the
        # replay (docs/DECISIONS.md D-009).
        assert record["occurred_at_ms"] in {1_750_000_000_400, 1_750_000_000_600}
        record_id = record["record_id"]
        assert isinstance(record_id, str)
        assert record_id.startswith(str(record["correlation_id"]))
