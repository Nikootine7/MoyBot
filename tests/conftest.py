"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from moybot.core.clock import FixedClock
from moybot.core.model.primitives import TimestampMs

FIXTURE_DIR = Path(__file__).parent / "fixtures"
GOLDEN_DIR = Path(__file__).parent / "golden"


@pytest.fixture
def fixture_dir() -> Path:
    """Directory containing replay fixtures."""
    return FIXTURE_DIR


@pytest.fixture
def golden_dir() -> Path:
    """Directory containing golden provenance files."""
    return GOLDEN_DIR


@pytest.fixture
def clock() -> FixedClock:
    """A deterministic clock starting at a fixed instant."""
    return FixedClock(TimestampMs(1_750_000_000_000))
