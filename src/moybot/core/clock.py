"""Time sources.

Time is injected rather than read from the ambient environment so that the pipeline stays
deterministic and testable (PROJECT_SPEC.md §10.9: decisions must be explainable from their
snapshot, which requires reproducible timestamps).
"""

from __future__ import annotations

import time
from typing import Protocol, final

from moybot.core.errors import NotConfiguredError
from moybot.core.model.primitives import TimestampMs

__all__ = ["Clock", "FixedClock", "ObservedTimeClock", "SourceTimeClock", "SystemClock"]


class Clock(Protocol):
    """Wall-clock and monotonic time source."""

    def now_ms(self) -> TimestampMs:
        """Wall-clock time in milliseconds since the Unix epoch."""

    def monotonic_ns(self) -> int:
        """Monotonic time in nanoseconds, for measuring durations."""


class ObservedTimeClock(Clock, Protocol):
    """A clock whose wall-clock time is supplied by the data source (docs/DECISIONS.md D-009)."""

    def observe(self, observed_at_ms: TimestampMs) -> None:
        """Report the time an observation was made at."""


@final
class SystemClock:
    """Clock backed by the operating system."""

    def now_ms(self) -> TimestampMs:
        return TimestampMs(time.time_ns() // 1_000_000)

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()


@final
class FixedClock:
    """Deterministic clock for tests and replay runs.

    Wall-clock time only advances when ``advance_ms`` is called, and monotonic time advances by
    a fixed step on every read so that measured durations are reproducible.
    """

    def __init__(self, start_ms: TimestampMs, monotonic_step_ns: int = 1_000) -> None:
        self._now_ms = start_ms
        self._monotonic_ns = 0
        self._step_ns = monotonic_step_ns

    def now_ms(self) -> TimestampMs:
        return self._now_ms

    def monotonic_ns(self) -> int:
        self._monotonic_ns += self._step_ns
        return self._monotonic_ns

    def advance_ms(self, delta_ms: int) -> None:
        self._now_ms = TimestampMs(self._now_ms + delta_ms)

    def set_now_ms(self, now_ms: TimestampMs) -> None:
        self._now_ms = now_ms


@final
class SourceTimeClock:
    """Clock whose wall-clock time is the latest observation time reported by the source.

    Replay runs judge staleness against the time the data was observed, not the time the replay
    happens to run (docs/DECISIONS.md D-009). Reading the time before any observation has been
    reported is an error rather than a guess: there is no defensible substitute.

    Time never moves backwards. An observation older than one already reported does not rewind
    the clock, so out-of-order observations cannot make later data look fresher than it is.
    """

    def __init__(self, monotonic_step_ns: int = 1_000) -> None:
        self._now_ms: TimestampMs | None = None
        self._monotonic_ns = 0
        self._step_ns = monotonic_step_ns

    def observe(self, observed_at_ms: TimestampMs) -> None:
        if self._now_ms is None or observed_at_ms > self._now_ms:
            self._now_ms = observed_at_ms

    def now_ms(self) -> TimestampMs:
        if self._now_ms is None:
            msg = "no observation time has been reported to the source clock yet"
            raise NotConfiguredError(msg)
        return self._now_ms

    def monotonic_ns(self) -> int:
        self._monotonic_ns += self._step_ns
        return self._monotonic_ns
