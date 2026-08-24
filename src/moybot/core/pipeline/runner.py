"""Pipeline runner (PROJECT_SPEC.md §2).

Runs the canonical pipeline for one observation at a time:

    CONTINUOUS DATA -> EVENT TRIGGER -> DELTA ANALYSIS -> CANDIDATE FILTERING ->
    HEAVY ANALYSIS -> SCORING -> FINAL PRE-TRADE VALIDATION -> ACTION

Properties this implementation is responsible for:

* an observation with no event does no expensive work (§2.2);
* candidate filtering runs per strategy, so Bot A and Bot B may look at the universe
  differently (§10.7);
* every stage outcome after an event is written to provenance, including rejections and
  cancellations (§4);
* identifiers are derived deterministically from the update, so a replay produces byte-identical
  provenance.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final

import structlog

from moybot.core.action.sink_port import ActionSink
from moybot.core.analysis.registry import HeavyAnalysisRegistry
from moybot.core.clock import Clock
from moybot.core.delta.differ import SnapshotDiffer
from moybot.core.errors import ModuleNotImplementedError
from moybot.core.events.registry import EventDetectorRegistry
from moybot.core.ingestion.source_port import MarketDataSource
from moybot.core.model.alert import Alert
from moybot.core.model.candidate import Candidate
from moybot.core.model.decision import Decision, DecisionOutcome, ValidationResult
from moybot.core.model.event import Event
from moybot.core.model.primitives import JsonValue, Pubkey, Slot, TimestampMs
from moybot.core.model.provenance import ProvenanceRecord
from moybot.core.model.snapshot import Snapshot
from moybot.core.model.update import MarketUpdate
from moybot.core.pipeline.stage import StageName
from moybot.core.pipeline.timing import Stopwatch
from moybot.core.snapshots.builder import SnapshotBuilder
from moybot.core.snapshots.store_port import ProvenanceStore, SnapshotStore
from moybot.core.state.cache_port import ContinuousStateCache
from moybot.core.strategy.strategy_port import Strategy
from moybot.core.validation.validator_port import PreTradeValidator

__all__ = ["PipelineRunner", "UpdateResult"]


@final
@dataclass(frozen=True, slots=True)
class UpdateResult:
    """Everything the pipeline produced for one observation."""

    mint: Pubkey
    slot: Slot
    events: tuple[Event, ...]
    decisions: tuple[Decision, ...]
    alerts: tuple[Alert, ...]
    records: tuple[ProvenanceRecord, ...]


@final
class PipelineRunner:
    """Wires the canonical stages together."""

    def __init__(
        self,
        cache: ContinuousStateCache,
        detectors: EventDetectorRegistry,
        snapshot_builder: SnapshotBuilder,
        snapshot_store: SnapshotStore,
        differ: SnapshotDiffer,
        heavy_analysis: HeavyAnalysisRegistry,
        strategies: Sequence[Strategy],
        validator: PreTradeValidator,
        action_sink: ActionSink,
        provenance_store: ProvenanceStore,
        clock: Clock,
    ) -> None:
        self._cache = cache
        self._detectors = detectors
        self._snapshot_builder = snapshot_builder
        self._snapshot_store = snapshot_store
        self._differ = differ
        self._heavy_analysis = heavy_analysis
        self._strategies = tuple(strategies)
        self._validator = validator
        self._action_sink = action_sink
        self._provenance_store = provenance_store
        self._clock = clock
        self._logger = structlog.get_logger("moybot.pipeline")

    async def process(self, update: MarketUpdate) -> UpdateResult:
        """Run the pipeline for one observation."""
        records: list[ProvenanceRecord] = []
        decisions: list[Decision] = []
        alerts: list[Alert] = []

        # The pre-update view is what DELTA ANALYSIS compares against: the delta is the change
        # this observation caused (§2.3), not the change since the last event.
        previous = self._snapshot_builder.capture(update.mint)
        with Stopwatch(self._clock) as cache_watch:
            self._cache.apply(update.to_patch())
        self._logger.debug(
            "continuous_data_applied",
            mint=update.mint,
            slot=int(update.slot),
            duration_us=cache_watch.duration_us,
            fields=[name for name, _ in update.metrics],
        )

        with Stopwatch(self._clock) as detect_watch:
            events = self._detectors.detect(update)
        if not events:
            self._logger.debug(
                "no_event",
                mint=update.mint,
                slot=int(update.slot),
                duration_us=detect_watch.duration_us,
            )
            return UpdateResult(
                mint=update.mint, slot=update.slot, events=(), decisions=(), alerts=(), records=()
            )

        for index, event in enumerate(events):
            correlation_id = f"{update.source}:{update.sequence}:{index}"
            event_records, event_decisions, event_alerts = self._process_event(
                update, event, correlation_id, detect_watch.duration_us, previous
            )
            records.extend(event_records)
            decisions.extend(event_decisions)
            alerts.extend(event_alerts)

        return UpdateResult(
            mint=update.mint,
            slot=update.slot,
            events=events,
            decisions=tuple(decisions),
            alerts=tuple(alerts),
            records=tuple(records),
        )

    async def run(self, updates: Sequence[MarketUpdate]) -> tuple[UpdateResult, ...]:
        """Run the pipeline over a finite batch of observations, in order."""
        results: list[UpdateResult] = []
        for update in updates:
            results.append(await self.process(update))
        return tuple(results)

    async def run_source(self, source: MarketDataSource) -> tuple[UpdateResult, ...]:
        """Run the pipeline over everything a data source yields, in source order."""
        results: list[UpdateResult] = []
        async for update in source.updates():
            results.append(await self.process(update))
        return tuple(results)

    def _process_event(
        self,
        update: MarketUpdate,
        event: Event,
        correlation_id: str,
        detect_duration_us: int,
        previous: Snapshot | None,
    ) -> tuple[tuple[ProvenanceRecord, ...], tuple[Decision, ...], tuple[Alert, ...]]:
        records: list[ProvenanceRecord] = []
        decisions: list[Decision] = []
        alerts: list[Alert] = []
        counter = _RecordCounter(correlation_id)

        records.append(
            self._record(
                counter,
                StageName.EVENT_TRIGGER,
                update.mint,
                update.slot,
                outcome=str(event.kind),
                duration_us=detect_duration_us,
                detail={"source": event.source, "detectors": list(self._detectors.detector_names)},
            )
        )

        with Stopwatch(self._clock) as snapshot_watch:
            snapshot = self._snapshot_builder.capture(
                update.mint, update.slot, update.observed_at_ms
            )
        if snapshot is None:
            records.append(
                self._record(
                    counter,
                    StageName.CONTINUOUS_DATA,
                    update.mint,
                    update.slot,
                    outcome="no_state",
                    duration_us=snapshot_watch.duration_us,
                    detail={"reason": "token has never been observed"},
                )
            )
            return tuple(records), (), ()
        self._snapshot_store.append(snapshot)
        records.append(
            self._record(
                counter,
                StageName.CONTINUOUS_DATA,
                update.mint,
                update.slot,
                outcome="captured",
                duration_us=snapshot_watch.duration_us,
                detail={
                    "observed_at_ms": int(snapshot.captured_at_ms),
                    "sequence": snapshot.sequence,
                    "reported_fields": [name for name, _ in update.metrics],
                },
            )
        )

        with Stopwatch(self._clock) as delta_watch:
            delta = self._differ.diff(previous, snapshot)
        records.append(
            self._record(
                counter,
                StageName.DELTA_ANALYSIS,
                update.mint,
                update.slot,
                outcome="empty" if delta.is_empty else "changed",
                duration_us=delta_watch.duration_us,
                detail={
                    "from_slot": int(delta.from_slot) if delta.from_slot is not None else None,
                    "to_slot": int(delta.to_slot),
                    "changed_paths": list(delta.changed_paths()),
                },
            )
        )

        base_candidate = Candidate(
            mint=update.mint,
            event=event,
            snapshot=snapshot,
            previous_snapshot=previous,
            delta=delta,
        )

        for strategy in self._strategies:
            strategy_records, decision, alert = self._run_strategy(
                strategy, base_candidate, counter, update.slot
            )
            records.extend(strategy_records)
            if decision is not None:
                decisions.append(decision)
            if alert is not None:
                alerts.append(alert)

        return tuple(records), tuple(decisions), tuple(alerts)

    def _run_strategy(
        self,
        strategy: Strategy,
        candidate: Candidate,
        counter: _RecordCounter,
        current_slot: Slot,
    ) -> tuple[tuple[ProvenanceRecord, ...], Decision | None, Alert | None]:
        records: list[ProvenanceRecord] = []

        with Stopwatch(self._clock) as filter_watch:
            filter_result = strategy.filters.run(candidate)
        records.append(
            self._record(
                counter,
                StageName.CANDIDATE_FILTERING,
                candidate.mint,
                candidate.snapshot.slot,
                outcome="accepted" if filter_result.accepted else "rejected",
                duration_us=filter_watch.duration_us,
                detail={
                    "strategy": strategy.name,
                    "rejected_by": filter_result.rejected_by,
                    "trace": [
                        {
                            "filter": verdict.filter_name,
                            "accepted": verdict.accepted,
                            "reason": verdict.reason,
                        }
                        for verdict in filter_result.trace
                    ],
                },
            )
        )
        if not filter_result.accepted:
            return tuple(records), None, None

        filtered = filter_result.candidate
        with Stopwatch(self._clock) as analysis_watch:
            try:
                features = self._heavy_analysis.analyze(filtered)
            except ModuleNotImplementedError as exc:
                records.append(
                    self._record(
                        counter,
                        StageName.HEAVY_ANALYSIS,
                        candidate.mint,
                        candidate.snapshot.slot,
                        outcome="module_not_implemented",
                        duration_us=analysis_watch.duration_us,
                        detail={"strategy": strategy.name, "error": str(exc)},
                    )
                )
                return tuple(records), None, None
        records.append(
            self._record(
                counter,
                StageName.HEAVY_ANALYSIS,
                candidate.mint,
                candidate.snapshot.slot,
                outcome="analyzed",
                duration_us=analysis_watch.duration_us,
                detail={
                    "strategy": strategy.name,
                    "enabled_modules": list(self._heavy_analysis.enabled),
                    "features": list(features.names()),
                },
            )
        )

        with Stopwatch(self._clock) as scoring_watch:
            decision = strategy.evaluate(filtered, features)
        records.append(
            self._record(
                counter,
                StageName.SCORING,
                candidate.mint,
                candidate.snapshot.slot,
                outcome=str(decision.outcome),
                duration_us=scoring_watch.duration_us,
                detail={
                    "strategy": strategy.name,
                    "reason": decision.reason,
                    "score": str(decision.score.value) if decision.score is not None else None,
                    "contributions": [
                        {
                            "feature": contribution.feature,
                            "value": str(contribution.value),
                            "weight": str(contribution.weight),
                            "contribution": str(contribution.contribution),
                        }
                        for contribution in (
                            decision.score.contributions if decision.score is not None else ()
                        )
                    ],
                },
            )
        )
        if decision.outcome is not DecisionOutcome.ADVANCE:
            return tuple(records), decision, None

        with Stopwatch(self._clock) as validation_watch:
            validation = self._validator.validate(filtered, decision, current_slot)
        records.append(
            self._record(
                counter,
                StageName.PRE_TRADE_VALIDATION,
                candidate.mint,
                candidate.snapshot.slot,
                outcome=str(validation.outcome),
                duration_us=validation_watch.duration_us,
                detail=_validation_detail(strategy.name, validation),
            )
        )
        if not validation.passed:
            return tuple(records), decision, None

        alert = Alert(
            correlation_id=counter.correlation_id,
            mint=candidate.mint,
            raised_at_ms=self._clock.now_ms(),
            decision=decision,
            validation=validation,
            candidate=filtered,
        )
        with Stopwatch(self._clock) as action_watch:
            self._action_sink.emit(alert)
        records.append(
            self._record(
                counter,
                StageName.ACTION,
                candidate.mint,
                candidate.snapshot.slot,
                outcome="alert_raised",
                duration_us=action_watch.duration_us,
                detail={"strategy": strategy.name, "sink": self._action_sink.name},
            )
        )
        return tuple(records), decision, alert

    def _record(
        self,
        counter: _RecordCounter,
        stage: StageName,
        mint: Pubkey,
        slot: Slot,
        outcome: str,
        duration_us: int,
        detail: dict[str, JsonValue],
    ) -> ProvenanceRecord:
        record = ProvenanceRecord(
            record_id=counter.next_id(stage),
            correlation_id=counter.correlation_id,
            stage=stage,
            mint=mint,
            occurred_at_ms=TimestampMs(self._clock.now_ms()),
            slot=slot,
            outcome=outcome,
            duration_us=duration_us,
            detail=detail,
        )
        self._provenance_store.append(record)
        self._logger.info(
            "stage_completed",
            record_id=record.record_id,
            correlation_id=record.correlation_id,
            stage=str(stage),
            mint=mint,
            outcome=outcome,
            duration_us=duration_us,
        )
        return record


def _validation_detail(strategy: str, validation: ValidationResult) -> dict[str, JsonValue]:
    """Record what final validation checked, so the outcome can be reconstructed (§4, §5)."""
    refresh = validation.refresh
    staleness = validation.staleness
    checked = validation.checked_snapshot
    return {
        "strategy": strategy,
        "reason": validation.reason,
        "breached_limit": validation.breached_limit,
        "refresh": (
            None
            if refresh is None
            else {
                "refresher": refresh.refresher,
                "available": refresh.available,
                "slot": int(refresh.slot) if refresh.slot is not None else None,
                "observed_at_ms": (
                    int(refresh.observed_at_ms) if refresh.observed_at_ms is not None else None
                ),
                "unavailable_reason": refresh.unavailable_reason,
            }
        ),
        "checked_snapshot": (
            None
            if checked is None
            else {
                "slot": int(checked.slot),
                "captured_at_ms": int(checked.captured_at_ms),
                "sequence": checked.sequence,
            }
        ),
        "staleness": (
            None
            if staleness is None
            else {
                "checked_at_ms": int(staleness.checked_at_ms),
                "age_ms": staleness.age_ms,
                "current_slot": int(staleness.current_slot),
                "slot_lag": staleness.slot_lag,
            }
        ),
        "compared": [
            {
                "field": comparison.field,
                "at_decision": comparison.at_decision,
                "at_validation": comparison.at_validation,
            }
            for comparison in validation.comparisons
        ],
    }


@final
class _RecordCounter:
    """Generates deterministic provenance record identifiers."""

    def __init__(self, correlation_id: str) -> None:
        self.correlation_id = correlation_id
        self._count = 0

    def next_id(self, stage: StageName) -> str:
        self._count += 1
        return f"{self.correlation_id}:{self._count:03d}:{stage}"
