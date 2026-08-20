"""Primitive value types and parsers.

The bounds enforced here are properties of Solana itself (base58-encoded 32-byte public keys,
non-negative slots), not domain thresholds. No trading, scoring or risk constant appears in
this module.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Final, NewType

__all__ = [
    "JsonValue",
    "Pubkey",
    "Slot",
    "TimestampMs",
    "parse_decimal",
    "parse_pubkey",
    "parse_slot",
    "parse_timestamp_ms",
]

Pubkey = NewType("Pubkey", str)
"""A Solana account address, base58-encoded."""

Slot = NewType("Slot", int)
"""A Solana slot number. Primary ordering key for on-chain state."""

TimestampMs = NewType("TimestampMs", int)
"""Wall-clock milliseconds since the Unix epoch."""

type JsonValue = str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None
"""Any value that survives a JSON round trip without loss."""

_BASE58_ALPHABET: Final[frozenset[str]] = frozenset(
    "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
)
_PUBKEY_MIN_LEN: Final[int] = 32
_PUBKEY_MAX_LEN: Final[int] = 44


def parse_pubkey(raw: str) -> Pubkey:
    """Validate and wrap a base58 Solana address."""
    if not _PUBKEY_MIN_LEN <= len(raw) <= _PUBKEY_MAX_LEN:
        msg = (
            f"invalid Solana address length {len(raw)}; expected "
            f"{_PUBKEY_MIN_LEN}-{_PUBKEY_MAX_LEN} base58 characters"
        )
        raise ValueError(msg)
    invalid = sorted(set(raw) - _BASE58_ALPHABET)
    if invalid:
        msg = f"invalid base58 characters in Solana address: {''.join(invalid)!r}"
        raise ValueError(msg)
    return Pubkey(raw)


def parse_slot(raw: int) -> Slot:
    """Validate and wrap a Solana slot number."""
    if raw < 0:
        msg = f"slot must be non-negative, got {raw}"
        raise ValueError(msg)
    return Slot(raw)


def parse_timestamp_ms(raw: int) -> TimestampMs:
    """Validate and wrap a millisecond wall-clock timestamp."""
    if raw < 0:
        msg = f"timestamp_ms must be non-negative, got {raw}"
        raise ValueError(msg)
    return TimestampMs(raw)


def parse_decimal(raw: str | int | Decimal) -> Decimal:
    """Parse an exact decimal quantity.

    ``Decimal`` is used for every quantity so that stored snapshots reproduce exactly what the
    system observed, without binary floating-point drift.
    """
    if isinstance(raw, Decimal):
        return raw
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        msg = f"cannot parse decimal from {raw!r}"
        raise ValueError(msg) from exc
