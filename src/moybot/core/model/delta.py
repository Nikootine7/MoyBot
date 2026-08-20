"""Deltas (PROJECT_SPEC.md §2.3).

A delta answers "what changed since the previous snapshot?". It records changes mechanically;
deciding which changes are *meaningful* requires criteria that PROJECT_SPEC.md §9 leaves open,
so no significance rule appears here.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import final

from moybot.core.model.primitives import Pubkey, Slot

__all__ = ["Delta", "DeltaValue", "FieldDelta"]

type DeltaValue = str | int | bool | Decimal | None
"""Comparable, serializable representation of a single field value."""


@final
@dataclass(frozen=True, slots=True)
class FieldDelta:
    """One changed field, addressed by its dotted path within the snapshot metrics."""

    path: str
    before: DeltaValue
    after: DeltaValue


@final
@dataclass(frozen=True, slots=True)
class Delta:
    """The set of field-level changes between two snapshots of one token."""

    mint: Pubkey
    from_slot: Slot | None
    to_slot: Slot
    changes: tuple[FieldDelta, ...]

    @property
    def is_empty(self) -> bool:
        """True when nothing changed between the two snapshots."""
        return not self.changes

    def changed_paths(self) -> tuple[str, ...]:
        """Dotted paths of all changed fields, in comparison order."""
        return tuple(change.path for change in self.changes)
