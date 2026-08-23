"""Error types shared by core components."""

from __future__ import annotations

__all__ = [
    "ModuleNotImplementedError",
    "MoybotError",
    "NotConfiguredError",
]


class MoybotError(Exception):
    """Base class for all MOYBOT errors."""


class NotConfiguredError(MoybotError):
    """Raised when a component is asked to run without required configuration.

    PROJECT_SPEC.md §9 leaves scoring weights, thresholds and risk values undecided. Components
    that need such a value must raise this error instead of substituting a default, so that a
    placeholder never becomes a de-facto requirement.
    """


class ModuleNotImplementedError(MoybotError):
    """Raised when a declared-but-unimplemented heavy-analysis module is enabled.

    PROJECT_SPEC.md §3 lists heavy-analysis categories, not implementations. Phase 1 registers
    the categories so the pipeline shape is real, but running one is an error.
    """
