"""Market data source port."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from moybot.core.model.update import MarketUpdate

__all__ = ["MarketDataSource"]


class MarketDataSource(Protocol):
    """Yields observations of the token universe."""

    @property
    def name(self) -> str:
        """Stable identifier recorded on every update."""

    def updates(self) -> AsyncIterator[MarketUpdate]:
        """Stream observations in source order."""
