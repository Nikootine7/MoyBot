"""Candidates (PROJECT_SPEC.md §2.4).

A candidate is a token that an event has pushed into the pipeline, bundled with the snapshot it
was captured from, the delta against the previous snapshot, and the filter trace that admitted
it. The bundle exists so that any later decision can be explained from it (§4).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from moybot.core.model.delta import Delta
from moybot.core.model.event import Event
from moybot.core.model.primitives import Pubkey
from moybot.core.model.snapshot import Snapshot

__all__ = ["Candidate", "FilterVerdict"]


@final
@dataclass(frozen=True, slots=True)
class FilterVerdict:
    """Outcome of one candidate filter."""

    filter_name: str
    accepted: bool
    reason: str | None = None


@final
@dataclass(frozen=True, slots=True)
class Candidate:
    """A token admitted for heavy analysis, with the evidence that produced it."""

    mint: Pubkey
    event: Event
    snapshot: Snapshot
    previous_snapshot: Snapshot | None
    delta: Delta
    filter_trace: tuple[FilterVerdict, ...] = ()
