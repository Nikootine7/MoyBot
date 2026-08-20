"""Token identity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from moybot.core.model.primitives import Pubkey

__all__ = ["Token"]


@final
@dataclass(frozen=True, slots=True)
class Token:
    """A Solana token, identified by its mint address (docs/DECISIONS.md D-001).

    Symbol and name are intentionally optional metadata: they are never part of a decision and
    are not guaranteed to be available from any data source.
    """

    mint: Pubkey
    symbol: str | None = None
    name: str | None = None
