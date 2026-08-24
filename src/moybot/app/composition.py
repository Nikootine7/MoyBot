"""Composition root.

Builds the pipeline from configuration. This is the only place where concrete implementations are
chosen, so that swapping the replay adapter for a real provider later touches one file.

The fresh-state refresher is supplied by the caller together with the clock, because both belong
to the data source (docs/DECISIONS.md D-009, D-011). With no refresher, final validation cancels
everything: there is no fallback to the state the decision was made on.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import final

from moybot.app.config import AppConfig, StrategyConfig
from moybot.core.action.log_sink import LogAlertSink
from moybot.core.action.sink_port import ActionSink
from moybot.core.analysis.registry import HeavyAnalysisRegistry, spec_category_modules
from moybot.core.clock import Clock, SystemClock
from moybot.core.delta.differ import SnapshotDiffer
from moybot.core.events.registry import DeclaredEventDetector, EventDetectorRegistry
from moybot.core.filtering.accept_all import AcceptAllFilter
from moybot.core.filtering.chain import FilterChain
from moybot.core.ingestion.refresh_port import StateRefresher
from moybot.core.pipeline.runner import PipelineRunner
from moybot.core.scoring.weighted import WeightedScorer
from moybot.core.snapshots.builder import SnapshotBuilder
from moybot.core.snapshots.file_store import FileProvenanceStore, FileSnapshotStore
from moybot.core.snapshots.store_port import ProvenanceStore, SnapshotStore
from moybot.core.state.memory_cache import InMemoryStateCache
from moybot.core.strategy.bot_a import BotA
from moybot.core.strategy.bot_b import BotB
from moybot.core.strategy.strategy_port import Strategy
from moybot.core.validation.material_deterioration import (
    DeteriorationPolicy,
    MaterialDeteriorationValidator,
    StalenessPolicy,
)

__all__ = ["Pipeline", "build_pipeline"]


@final
@dataclass(frozen=True, slots=True)
class Pipeline:
    """The assembled pipeline and the collaborators a caller may need to inspect."""

    runner: PipelineRunner
    cache: InMemoryStateCache
    snapshot_store: SnapshotStore
    provenance_store: ProvenanceStore
    strategies: tuple[Strategy, ...]
    action_sink: ActionSink


def _weights(config: StrategyConfig) -> dict[str, Decimal] | None:
    return dict(config.weights) if config.weights else None


def build_pipeline(
    config: AppConfig,
    clock: Clock | None = None,
    refresher: StateRefresher | None = None,
    action_sink: ActionSink | None = None,
    snapshot_store: SnapshotStore | None = None,
    provenance_store: ProvenanceStore | None = None,
    data_dir: Path | None = None,
) -> Pipeline:
    """Assemble the Phase 1 pipeline."""
    resolved_clock: Clock = clock if clock is not None else SystemClock()
    root = data_dir if data_dir is not None else config.storage.data_dir
    snapshots: SnapshotStore = (
        snapshot_store if snapshot_store is not None else FileSnapshotStore(root)
    )
    provenance: ProvenanceStore = (
        provenance_store if provenance_store is not None else FileProvenanceStore(root)
    )
    sink: ActionSink = action_sink if action_sink is not None else LogAlertSink()

    cache = InMemoryStateCache()
    builder = SnapshotBuilder(cache)

    strategies: list[Strategy] = []
    if config.strategies.bot_a.enabled:
        strategies.append(
            BotA(
                scorer=WeightedScorer("bot_a_weighted", _weights(config.strategies.bot_a)),
                filters=FilterChain([AcceptAllFilter()]),
                score_threshold=config.strategies.bot_a.score_threshold,
                hard_rejection_rules=(),
            )
        )
    if config.strategies.bot_b.enabled:
        strategies.append(
            BotB(
                scorer=WeightedScorer("bot_b_weighted", _weights(config.strategies.bot_b)),
                filters=FilterChain([AcceptAllFilter()]),
                score_threshold=config.strategies.bot_b.score_threshold,
            )
        )

    staleness = config.validation.staleness
    deterioration = config.validation.deterioration
    validator = MaterialDeteriorationValidator(
        builder=builder,
        cache=cache,
        clock=resolved_clock,
        refresher=refresher,
        staleness_policy=(
            StalenessPolicy(
                max_snapshot_age_ms=staleness.max_snapshot_age_ms,
                max_slot_lag=staleness.max_slot_lag,
            )
            if staleness is not None
            else None
        ),
        deterioration_policy=(
            DeteriorationPolicy(
                max_price_drop_fraction=deterioration.max_price_drop_fraction,
                max_liquidity_drop_fraction=deterioration.max_liquidity_drop_fraction,
                max_slippage_bps=deterioration.max_slippage_bps,
                max_sell_pressure_ratio=deterioration.max_sell_pressure_ratio,
                cancel_on_dev_sold=deterioration.cancel_on_dev_sold,
                cancel_on_smart_wallet_exit=deterioration.cancel_on_smart_wallet_exit,
                cancel_on_lp_supply_change=deterioration.cancel_on_lp_supply_change,
            )
            if deterioration is not None
            else None
        ),
    )

    runner = PipelineRunner(
        cache=cache,
        detectors=EventDetectorRegistry([DeclaredEventDetector()]),
        snapshot_builder=builder,
        snapshot_store=snapshots,
        differ=SnapshotDiffer(),
        heavy_analysis=HeavyAnalysisRegistry(
            modules=spec_category_modules(),
            enabled=config.heavy_analysis.enabled_modules,
        ),
        strategies=strategies,
        validator=validator,
        action_sink=sink,
        provenance_store=provenance,
        clock=resolved_clock,
    )
    return Pipeline(
        runner=runner,
        cache=cache,
        snapshot_store=snapshots,
        provenance_store=provenance,
        strategies=tuple(strategies),
        action_sink=sink,
    )
