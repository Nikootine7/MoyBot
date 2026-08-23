"""File-backed snapshot and provenance stores."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from moybot.core.model.primitives import Slot, TimestampMs
from moybot.core.model.provenance import ProvenanceRecord
from moybot.core.pipeline.stage import StageName
from moybot.core.snapshots.file_store import FileProvenanceStore, FileSnapshotStore
from tests.support import MINT_A, metrics, snapshot


def test_snapshot_is_appended_as_ndjson_partitioned_by_mint_and_date(tmp_path: Path) -> None:
    store = FileSnapshotStore(tmp_path)
    store.append(snapshot())
    store.append(snapshot(slot=101, sequence=1, token_metrics=metrics(price=Decimal("2"))))
    path = tmp_path / "snapshots" / MINT_A / "2025-06-15.ndjson"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["mint"] == MINT_A
    assert first["slot"] == 100
    assert first["metrics"]["price"] == "1"


def test_exact_quantities_survive_the_round_trip(tmp_path: Path) -> None:
    store = FileSnapshotStore(tmp_path)
    store.append(snapshot(token_metrics=metrics(price=Decimal("0.00000410"))))
    path = tmp_path / "snapshots" / MINT_A / "2025-06-15.ndjson"
    record = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert record["metrics"]["price"] == "0.00000410"


def test_latest_returns_the_last_appended_snapshot(tmp_path: Path) -> None:
    store = FileSnapshotStore(tmp_path)
    assert store.latest(MINT_A) is None
    store.append(snapshot())
    newer = snapshot(slot=101, sequence=1)
    store.append(newer)
    assert store.latest(MINT_A) == newer


def test_provenance_is_appended_as_ndjson_partitioned_by_date(tmp_path: Path) -> None:
    store = FileProvenanceStore(tmp_path)
    store.append(
        ProvenanceRecord(
            record_id="corr:001:event_trigger",
            correlation_id="corr",
            stage=StageName.EVENT_TRIGGER,
            mint=MINT_A,
            occurred_at_ms=TimestampMs(1_750_000_000_000),
            slot=Slot(100),
            outcome="smart_wallet_buy",
            duration_us=12,
            detail={"source": "replay"},
        )
    )
    path = tmp_path / "provenance" / "2025-06-15.ndjson"
    record = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert record["stage"] == "event_trigger"
    assert record["detail"] == {"source": "replay"}
