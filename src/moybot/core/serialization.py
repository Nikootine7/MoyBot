"""JSON encoding of domain objects.

Snapshots and provenance records are stored as newline-delimited JSON (docs/DECISIONS.md D-005)
because auditability matters more than compactness in Phase 1. Exact quantities are encoded as
strings so that a stored snapshot reproduces exactly what was observed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from enum import Enum

from moybot.core.model.primitives import JsonValue

__all__ = ["to_json_value"]


def to_json_value(value: object) -> JsonValue:
    """Convert a domain object into a losslessly JSON-serializable value."""
    if value is None or isinstance(value, bool | str | int | float):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return to_json_value(value.value)
    if is_dataclass(value) and not isinstance(value, type):
        return {key: to_json_value(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): to_json_value(item) for key, item in value.items()}
    if isinstance(value, Sequence):
        return [to_json_value(item) for item in value]
    msg = f"cannot serialize value of type {type(value).__name__}"
    raise TypeError(msg)
