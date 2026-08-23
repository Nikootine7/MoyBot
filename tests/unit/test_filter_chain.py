"""Filter chain."""

from __future__ import annotations

from moybot.core.filtering.accept_all import AcceptAllFilter
from moybot.core.filtering.chain import FilterChain
from tests.support import RecordingFilter, RejectingFilter, candidate


def test_empty_chain_accepts() -> None:
    result = FilterChain([]).run(candidate())
    assert result.accepted
    assert result.trace == ()


def test_accept_all_is_recorded_in_the_trace() -> None:
    result = FilterChain([AcceptAllFilter()]).run(candidate())
    assert result.accepted
    assert [verdict.filter_name for verdict in result.trace] == ["accept_all"]
    assert result.candidate.filter_trace == result.trace


def test_chain_short_circuits_at_first_rejection() -> None:
    downstream = RecordingFilter("downstream")
    result = FilterChain([AcceptAllFilter(), RejectingFilter(), downstream]).run(candidate())
    assert not result.accepted
    assert result.rejected_by == "rejecting"
    assert downstream.calls == 0
    assert [verdict.filter_name for verdict in result.trace] == ["accept_all", "rejecting"]


def test_rejection_carries_a_reason() -> None:
    result = FilterChain([RejectingFilter()]).run(candidate())
    assert result.trace[-1].reason == "test rejection"
