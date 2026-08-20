"""File-backed snapshot and provenance stores (docs/DECISIONS.md D-005).

Records are appended as newline-delimited JSON, partitioned by mint and UTC date. Retention and
pruning are OPEN QUESTIONS (PROJECT_SPEC.md §9); nothing here deletes data.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import final

from moybot.core.model.primitives import Pubkey
from moybot.core.model.provenance import ProvenanceRecord
from moybot.core.model.snapshot import Snapshot
from moybot.core.serialization import to_json_value

__all__ = [
    "FileProvenanceStore",
    "FileSnapshotStore",
    "InMemoryProvenanceStore",
    "InMemorySnapshotStore",
]


def _utc_date(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).strftime("%Y-%m-%d")


def _append_json_line(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(to_json_value(payload), separators=(",", ":"), sort_keys=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")


@final
class FileSnapshotStore:
    """Appends snapshots to ``<data_dir>/snapshots/<mint>/<date>.ndjson``."""

    def __init__(self, data_dir: Path) -> None:
        self._root = data_dir / "snapshots"
        self._latest: dict[Pubkey, Snapshot] = {}

    def append(self, snapshot: Snapshot) -> None:
        path = self._root / snapshot.mint / f"{_utc_date(int(snapshot.captured_at_ms))}.ndjson"
        _append_json_line(path, snapshot)
        self._latest[snapshot.mint] = snapshot

    def latest(self, mint: Pubkey) -> Snapshot | None:
        return self._latest.get(mint)


@final
class FileProvenanceStore:
    """Appends provenance records to ``<data_dir>/provenance/<date>.ndjson``."""

    def __init__(self, data_dir: Path) -> None:
        self._root = data_dir / "provenance"

    def append(self, record: ProvenanceRecord) -> None:
        path = self._root / f"{_utc_date(int(record.occurred_at_ms))}.ndjson"
        _append_json_line(path, record)


@final
class InMemorySnapshotStore:
    """Snapshot store for tests and dry runs."""

    def __init__(self) -> None:
        self.appended: list[Snapshot] = []
        self._latest: dict[Pubkey, Snapshot] = {}

    def append(self, snapshot: Snapshot) -> None:
        self.appended.append(snapshot)
        self._latest[snapshot.mint] = snapshot

    def latest(self, mint: Pubkey) -> Snapshot | None:
        return self._latest.get(mint)


@final
class InMemoryProvenanceStore:
    """Provenance store for tests and dry runs."""

    def __init__(self) -> None:
        self.records: list[ProvenanceRecord] = []

    def append(self, record: ProvenanceRecord) -> None:
        self.records.append(record)
