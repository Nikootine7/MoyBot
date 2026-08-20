"""Property-based differ tests.

The differ must be total over the cached fields of PROJECT_SPEC.md §2.1 and must never report a
change that did not happen.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from moybot.core.delta.differ import SnapshotDiffer, flatten_metrics
from moybot.core.model.metrics import HolderDistribution, LpState, TokenMetrics, TokenState
from tests.support import WALLET_A, WALLET_B, snapshot

_decimals = st.decimals(
    min_value=Decimal("0"), max_value=Decimal("1000000"), allow_nan=False, allow_infinity=False
)
_optional_decimals = st.none() | _decimals
_optional_ints = st.none() | st.integers(min_value=0, max_value=1_000_000)

_metrics = st.builds(
    TokenMetrics,
    price=_optional_decimals,
    price_change=_optional_decimals,
    volume=_optional_decimals,
    buy_volume=_optional_decimals,
    sell_volume=_optional_decimals,
    liquidity=_optional_decimals,
    slippage_bps=_optional_decimals,
    holders=st.builds(
        HolderDistribution,
        holder_count=_optional_ints,
        top_holder_shares=st.lists(_decimals, max_size=3).map(tuple),
    ),
    dev_transaction_count=_optional_ints,
    dev_sold=st.none() | st.booleans(),
    smart_wallet_transaction_count=_optional_ints,
    smart_wallet_addresses=st.lists(st.sampled_from([WALLET_A, WALLET_B]), max_size=2).map(tuple),
    wallet_cluster_ids=st.lists(st.sampled_from(["c1", "c2"]), max_size=2).map(tuple),
    token_state=st.builds(TokenState, supply=_optional_decimals, decimals=_optional_ints),
    lp_state=st.builds(LpState, lp_token_supply=_optional_decimals),
)


@given(_metrics)
def test_diff_of_a_snapshot_with_itself_is_empty(token_metrics: TokenMetrics) -> None:
    current = snapshot(token_metrics=token_metrics)
    assert SnapshotDiffer().diff(current, current).is_empty


@given(_metrics)
def test_flatten_is_total_over_metric_fields(token_metrics: TokenMetrics) -> None:
    paths = flatten_metrics(token_metrics)
    for field in dataclasses.fields(TokenMetrics):
        assert any(path == field.name or path.startswith(f"{field.name}.") for path in paths)


@given(_metrics, _metrics)
def test_reported_changes_are_real_changes(first: TokenMetrics, second: TokenMetrics) -> None:
    before = flatten_metrics(first)
    after = flatten_metrics(second)
    delta = SnapshotDiffer().diff(
        snapshot(token_metrics=first), snapshot(slot=101, token_metrics=second)
    )
    for change in delta.changes:
        assert before.get(change.path) != after.get(change.path)
    unchanged = {
        path for path in before.keys() | after.keys() if before.get(path) == after.get(path)
    }
    assert unchanged.isdisjoint(set(delta.changed_paths()))
