"""Primitive parsers."""

from __future__ import annotations

from decimal import Decimal

import pytest

from moybot.core.model.primitives import (
    parse_decimal,
    parse_pubkey,
    parse_slot,
    parse_timestamp_ms,
)


def test_parse_pubkey_accepts_base58_address() -> None:
    address = "MoyMintAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    assert parse_pubkey(address) == address


@pytest.mark.parametrize("raw", ["short", "M" * 45])
def test_parse_pubkey_rejects_wrong_length(raw: str) -> None:
    with pytest.raises(ValueError, match="invalid Solana address length"):
        parse_pubkey(raw)


def test_parse_pubkey_rejects_non_base58_characters() -> None:
    with pytest.raises(ValueError, match="invalid base58 characters"):
        parse_pubkey("0OIl" + "A" * 36)


def test_parse_slot_rejects_negative() -> None:
    with pytest.raises(ValueError, match="slot must be non-negative"):
        parse_slot(-1)


def test_parse_timestamp_rejects_negative() -> None:
    with pytest.raises(ValueError, match="timestamp_ms must be non-negative"):
        parse_timestamp_ms(-1)


def test_parse_decimal_is_exact() -> None:
    assert parse_decimal("0.00000410") == Decimal("0.00000410")
    assert str(parse_decimal("0.00000410")) == "0.00000410"


def test_parse_decimal_rejects_garbage() -> None:
    with pytest.raises(ValueError, match="cannot parse decimal"):
        parse_decimal("not-a-number")
