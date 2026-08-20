"""Ports for snapshot and provenance storage (PROJECT_SPEC.md §4)."""

from __future__ import annotations

from typing import Protocol

from moybot.core.model.primitives import Pubkey
from moybot.core.model.provenance import ProvenanceRecord
from moybot.core.model.snapshot import Snapshot

__all__ = ["ProvenanceStore", "SnapshotStore"]


class SnapshotStore(Protocol):
    """Append-only snapshot storage with fast access to the latest snapshot per token."""

    def append(self, snapshot: Snapshot) -> None:
        """Persist a snapshot."""

    def latest(self, mint: Pubkey) -> Snapshot | None:
        """Most recently appended snapshot for one token, or ``None``."""


class ProvenanceStore(Protocol):
    """Append-only storage for decision provenance.

    Every stage outcome after an event is recorded here, including rejections and cancellations,
    so that any decision can be reconstructed (PROJECT_SPEC.md §4).
    """

    def append(self, record: ProvenanceRecord) -> None:
        """Persist a provenance record."""
