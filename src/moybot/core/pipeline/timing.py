"""Stage timing.

Timings are recorded in provenance and logs. PROJECT_SPEC.md §9 leaves the latency target open,
so Phase 1 measures and reports but never asserts or enforces a budget.
"""

from __future__ import annotations

from types import TracebackType
from typing import final

from moybot.core.clock import Clock

__all__ = ["Stopwatch"]


@final
class Stopwatch:
    """Measures elapsed monotonic time in microseconds."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._started_ns = clock.monotonic_ns()
        self._stopped_ns: int | None = None

    def __enter__(self) -> Stopwatch:
        self._started_ns = self._clock.monotonic_ns()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._stopped_ns = self._clock.monotonic_ns()

    @property
    def duration_us(self) -> int:
        """Elapsed time in microseconds, measured to the stop point or to now."""
        stopped_ns = (
            self._stopped_ns if self._stopped_ns is not None else self._clock.monotonic_ns()
        )
        return (stopped_ns - self._started_ns) // 1_000
