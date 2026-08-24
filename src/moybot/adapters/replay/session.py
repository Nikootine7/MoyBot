"""Wiring for a replay run.

A replay needs three collaborators that only make sense together: the source, the refresher that
serves the fresh state the source declares, and the clock that takes its time from both
(docs/DECISIONS.md D-009). Building them separately is how the Phase 1 CLI ended up judging 2025
fixture data against the current wall clock.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import final

from moybot.adapters.replay.refresher import ReplayStateRefresher
from moybot.adapters.replay.source import ReplayDataSource
from moybot.core.clock import SourceTimeClock

__all__ = ["ReplaySession", "open_replay"]


@final
@dataclass(frozen=True, slots=True)
class ReplaySession:
    """Everything a replay run needs, wired to the same fixture."""

    source: ReplayDataSource
    refresher: ReplayStateRefresher
    clock: SourceTimeClock


def open_replay(path: Path) -> ReplaySession:
    """Open a fixture as a fully wired, deterministic replay run."""
    clock = SourceTimeClock()
    refresher = ReplayStateRefresher(clock=clock)
    source = ReplayDataSource.from_file(path, refresher=refresher, clock=clock)
    return ReplaySession(source=source, refresher=refresher, clock=clock)
