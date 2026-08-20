"""Replay data source (docs/DECISIONS.md D-004).

Yields fixture updates in file order. Deterministic and offline: no network call, no provider
client, no clock dependency.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from pathlib import Path
from typing import final

from moybot.adapters.replay.fixtures import load_fixture
from moybot.core.model.update import MarketUpdate

__all__ = ["ReplayDataSource"]


@final
class ReplayDataSource:
    """A market data source backed by a fixture file."""

    def __init__(self, name: str, updates: Sequence[MarketUpdate]) -> None:
        self._name = name
        self._updates = tuple(updates)

    @classmethod
    def from_file(cls, path: Path) -> ReplayDataSource:
        """Build a source from a fixture on disk."""
        fixture = load_fixture(path)
        return cls(name=f"replay:{fixture.name}", updates=fixture.to_updates())

    @property
    def name(self) -> str:
        return self._name

    @property
    def batch(self) -> tuple[MarketUpdate, ...]:
        """All updates, for callers that prefer a finite batch over a stream."""
        return self._updates

    async def updates(self) -> AsyncIterator[MarketUpdate]:
        for update in self._updates:
            yield update
