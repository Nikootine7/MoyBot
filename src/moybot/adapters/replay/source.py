"""Replay data source (docs/DECISIONS.md D-004).

Yields fixture updates in file order. Deterministic and offline: no network call and no provider
client.

Two collaborators may be attached (docs/DECISIONS.md D-009, D-010). Both are optional, and both
fail closed when absent: without a clock nothing supplies observation time, and without a
refresher validation finds no fresh state and cancels.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from pathlib import Path
from typing import final

from moybot.adapters.replay.fixtures import ReplayEntry, load_fixture
from moybot.adapters.replay.refresher import ReplayStateRefresher
from moybot.core.clock import ObservedTimeClock
from moybot.core.model.update import MarketUpdate

__all__ = ["ReplayDataSource"]


@final
class ReplayDataSource:
    """A market data source backed by a fixture file."""

    def __init__(
        self,
        name: str,
        entries: Sequence[ReplayEntry],
        refresher: ReplayStateRefresher | None = None,
        clock: ObservedTimeClock | None = None,
    ) -> None:
        self._name = name
        self._entries = tuple(entries)
        self._refresher = refresher
        self._clock = clock

    @classmethod
    def from_file(
        cls,
        path: Path,
        refresher: ReplayStateRefresher | None = None,
        clock: ObservedTimeClock | None = None,
    ) -> ReplayDataSource:
        """Build a source from a fixture on disk."""
        fixture = load_fixture(path)
        return cls(
            name=f"replay:{fixture.name}",
            entries=fixture.to_entries(),
            refresher=refresher,
            clock=clock,
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def batch(self) -> tuple[MarketUpdate, ...]:
        """All updates, for callers that prefer a finite batch over a stream."""
        return tuple(entry.update for entry in self._entries)

    async def updates(self) -> AsyncIterator[MarketUpdate]:
        for entry in self._entries:
            if self._clock is not None:
                self._clock.observe(entry.update.observed_at_ms)
            if self._refresher is not None:
                self._refresher.publish(entry.update.mint, entry.validation_state)
            yield entry.update
