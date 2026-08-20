"""Snapshot differ."""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from moybot.core.delta.differ import SnapshotDiffer, flatten_metrics
from moybot.core.model.metrics import HolderDistribution, TokenMetrics
from tests.support import MINT_A, MINT_B, metrics, snapshot


def test_identical_snapshots_produce_empty_delta() -> None:
    current = snapshot()
    delta = SnapshotDiffer().diff(snapshot(), current)
    assert delta.is_empty
    assert delta.changed_paths() == ()


def test_missing_previous_snapshot_produces_empty_delta() -> None:
    delta = SnapshotDiffer().diff(None, snapshot())
    assert delta.is_empty
    assert delta.from_slot is None


def test_changed_field_is_reported() -> None:
    delta = SnapshotDiffer().diff(
        snapshot(), snapshot(slot=101, token_metrics=metrics(price=Decimal("2")))
    )
    assert delta.changed_paths() == ("price",)
    change = delta.changes[0]
    assert (change.before, change.after) == (Decimal("1"), Decimal("2"))


def test_newly_known_field_is_reported_as_added() -> None:
    delta = SnapshotDiffer().diff(
        snapshot(token_metrics=metrics(dev_transaction_count=None)),
        snapshot(token_metrics=metrics(dev_transaction_count=3)),
    )
    assert delta.changed_paths() == ("dev_transaction_count",)
    assert delta.changes[0].before is None


def test_now_unknown_field_is_reported_as_removed() -> None:
    delta = SnapshotDiffer().diff(
        snapshot(token_metrics=metrics(dev_transaction_count=3)),
        snapshot(token_metrics=metrics(dev_transaction_count=None)),
    )
    assert delta.changes[0].after is None


def test_sequence_length_change_is_visible() -> None:
    delta = SnapshotDiffer().diff(
        snapshot(
            token_metrics=metrics(
                holders=HolderDistribution(holder_count=1, top_holder_shares=(Decimal("0.5"),))
            )
        ),
        snapshot(
            token_metrics=metrics(
                holders=HolderDistribution(
                    holder_count=1, top_holder_shares=(Decimal("0.5"), Decimal("0.2"))
                )
            )
        ),
    )
    assert "holders.top_holder_shares.length" in delta.changed_paths()
    assert "holders.top_holder_shares[1]" in delta.changed_paths()


def test_changes_are_sorted_by_path() -> None:
    delta = SnapshotDiffer().diff(
        snapshot(),
        snapshot(token_metrics=metrics(price=Decimal("2"), liquidity=Decimal("2000"))),
    )
    assert list(delta.changed_paths()) == sorted(delta.changed_paths())


def test_different_mints_cannot_be_diffed() -> None:
    with pytest.raises(ValueError, match="different mints"):
        SnapshotDiffer().diff(snapshot(mint=MINT_A), snapshot(mint=MINT_B))


def test_flatten_covers_every_metric_field() -> None:
    paths = flatten_metrics(metrics())
    for field in dataclasses.fields(TokenMetrics):
        assert any(
            path == field.name or path.startswith(f"{field.name}.") for path in paths
        ), f"metric field {field.name} is not covered by the differ"
