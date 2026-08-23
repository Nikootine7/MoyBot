"""Replay fixtures and source."""

from __future__ import annotations

import asyncio
import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from moybot.adapters.replay.fixtures import load_fixture
from moybot.adapters.replay.source import ReplayDataSource
from moybot.core.model.update import MarketUpdate


def test_fixture_loads_updates_in_file_order(fixture_dir: Path) -> None:
    source = ReplayDataSource.from_file(fixture_dir / "smart_wallet_buy.json")
    assert source.name == "replay:smart_wallet_buy"
    assert [int(update.slot) for update in source.batch] == [100, 101]
    assert [update.sequence for update in source.batch] == [0, 1]


def test_only_reported_metric_fields_are_carried(fixture_dir: Path) -> None:
    source = ReplayDataSource.from_file(fixture_dir / "smart_wallet_buy.json")
    reported = {name for name, _ in source.batch[1].metrics}
    assert "price" in reported
    assert "dev_sold" not in reported


def test_reported_decimals_are_exact(fixture_dir: Path) -> None:
    source = ReplayDataSource.from_file(fixture_dir / "smart_wallet_buy.json")
    fields = dict(source.batch[0].metrics)
    assert fields["price"] == Decimal("0.00000410")


def test_events_come_only_from_the_fixture(fixture_dir: Path) -> None:
    with_event = ReplayDataSource.from_file(fixture_dir / "smart_wallet_buy.json")
    without_event = ReplayDataSource.from_file(fixture_dir / "no_event.json")
    assert [event.kind for event in with_event.batch[1].declared_events] == ["smart_wallet_buy"]
    assert with_event.batch[0].declared_events == ()
    assert without_event.batch[0].declared_events == ()


def test_async_iteration_matches_the_batch(fixture_dir: Path) -> None:
    source = ReplayDataSource.from_file(fixture_dir / "smart_wallet_buy.json")

    async def collect() -> tuple[MarketUpdate, ...]:
        return tuple([update async for update in source.updates()])

    assert asyncio.run(collect()) == source.batch


def test_unsupported_schema_version_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "future.json"
    path.write_text(json.dumps({"schema_version": 99, "name": "future"}), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported fixture schema_version"):
        load_fixture(path)


def test_unknown_fixture_field_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps({"schema_version": 1, "name": "bad", "unexpected": True}), encoding="utf-8"
    )
    with pytest.raises(ValidationError):
        load_fixture(path)


def test_invalid_mint_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad_mint.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "name": "bad_mint",
                "updates": [{"mint": "nope", "slot": 1, "observed_at_ms": 1}],
            }
        ),
        encoding="utf-8",
    )
    fixture = load_fixture(path)
    with pytest.raises(ValueError, match="invalid Solana address length"):
        fixture.to_updates()
