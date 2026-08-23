"""Snapshot differ (PROJECT_SPEC.md §2.3).

The differ answers "what changed since the previous snapshot?" mechanically and totally: every
metric field of PROJECT_SPEC.md §2.1 is compared, and only actual changes are reported.

It deliberately contains no notion of significance. Deciding which changes matter needs criteria
that PROJECT_SPEC.md §9 leaves open, so that judgement belongs to configured filters and
scorers, not to the differ.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import asdict
from decimal import Decimal
from enum import Enum
from typing import final

from moybot.core.model.delta import Delta, DeltaValue, FieldDelta
from moybot.core.model.metrics import TokenMetrics
from moybot.core.model.snapshot import Snapshot

__all__ = ["SnapshotDiffer", "flatten_metrics"]


def _as_delta_value(value: object) -> DeltaValue:
    if value is None or isinstance(value, bool | int | str | Decimal):
        return value
    if isinstance(value, Enum):
        return _as_delta_value(value.value)
    if isinstance(value, float):
        return Decimal(str(value))
    msg = f"cannot compare value of type {type(value).__name__}"
    raise TypeError(msg)


def _walk(prefix: str, value: object) -> Iterator[tuple[str, DeltaValue]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            yield from _walk(child, item)
        return
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        yield (f"{prefix}.length", len(value))
        for index, item in enumerate(value):
            yield from _walk(f"{prefix}[{index}]", item)
        return
    yield (prefix, _as_delta_value(value))


def flatten_metrics(metrics: TokenMetrics) -> dict[str, DeltaValue]:
    """Flatten metrics into dotted paths, e.g. ``holders.top_holder_shares[0]``.

    Sequences also emit a ``.length`` entry so that appearing or disappearing entries are visible
    as a change rather than only as shifted indices.
    """
    return dict(_walk("", asdict(metrics)))


@final
class SnapshotDiffer:
    """Computes field-level deltas between two snapshots of the same token."""

    def diff(self, previous: Snapshot | None, current: Snapshot) -> Delta:
        """Compare two snapshots.

        A missing previous snapshot yields an empty delta rather than reporting every field as
        changed: "first observation" is not the same as "everything changed".
        """
        if previous is None:
            return Delta(mint=current.mint, from_slot=None, to_slot=current.slot, changes=())
        if previous.mint != current.mint:
            msg = f"cannot diff snapshots of different mints: {previous.mint} vs {current.mint}"
            raise ValueError(msg)
        before = flatten_metrics(previous.metrics)
        after = flatten_metrics(current.metrics)
        changes: list[FieldDelta] = []
        for path in sorted(before.keys() | after.keys()):
            old = before.get(path)
            new = after.get(path)
            if old != new:
                changes.append(FieldDelta(path=path, before=old, after=new))
        return Delta(
            mint=current.mint,
            from_slot=previous.slot,
            to_slot=current.slot,
            changes=tuple(changes),
        )
