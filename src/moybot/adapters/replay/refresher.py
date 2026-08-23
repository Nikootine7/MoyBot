"""Replay implementation of the fresh-state read port (docs/DECISIONS.md D-010, D-011).

The refresher answers "what does the token look like right now?" with the ``validation_state``
the currently replayed observation declared. Nothing is derived, interpolated, or extrapolated:
if the scenario declares no fresh state, the refresh is unavailable and validation cancels.

Offline and deterministic: no network call and no provider client.
"""

from __future__ import annotations

from typing import final

from moybot.core.clock import ObservedTimeClock
from moybot.core.ingestion.refresh_port import RefreshedState, RefreshResult, RefreshUnavailable
from moybot.core.model.primitives import Pubkey

__all__ = ["ReplayStateRefresher"]

_NAME = "replay_validation_state"


@final
class ReplayStateRefresher:
    """Serves the fresh state declared alongside the observation being replayed.

    The declared state is published by the replay source as each observation is yielded, so a
    refresh can only ever return state belonging to the observation under evaluation.
    """

    def __init__(self, clock: ObservedTimeClock | None = None) -> None:
        self._states: dict[Pubkey, RefreshedState] = {}
        self._clock = clock

    @property
    def name(self) -> str:
        return _NAME

    def publish(self, mint: Pubkey, state: RefreshedState | None) -> None:
        """Declare the fresh state for ``mint``, or withdraw it when the scenario declares none."""
        if state is None:
            self._states.pop(mint, None)
            return
        self._states[mint] = state

    def refresh(self, mint: Pubkey) -> RefreshResult:
        state = self._states.get(mint)
        if state is None:
            return RefreshUnavailable(
                mint=mint, reason="the replayed observation declared no validation-time state"
            )
        if self._clock is not None:
            self._clock.observe(state.observed_at_ms)
        return state
