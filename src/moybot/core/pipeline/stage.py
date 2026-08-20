"""Canonical pipeline stages.

The names below are exactly the stages of PROJECT_SPEC.md §2, in order, so that code, logs and
provenance records all speak the specification's vocabulary.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["StageName"]


class StageName(StrEnum):
    """A stage of the canonical pipeline (PROJECT_SPEC.md §2)."""

    CONTINUOUS_DATA = "continuous_data"
    EVENT_TRIGGER = "event_trigger"
    DELTA_ANALYSIS = "delta_analysis"
    CANDIDATE_FILTERING = "candidate_filtering"
    HEAVY_ANALYSIS = "heavy_analysis"
    SCORING = "scoring"
    PRE_TRADE_VALIDATION = "pre_trade_validation"
    ACTION = "action"
