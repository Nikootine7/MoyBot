"""Heavy-analysis registry and Phase 1 stubs (PROJECT_SPEC.md §3).

The categories below are quoted from PROJECT_SPEC.md §3. They are registered so that the
pipeline shape and configuration surface are real, and they are disabled by default. Enabling one
raises ``ModuleNotImplementedError`` rather than returning a fabricated feature.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Final, final

from moybot.core.analysis.module_port import HeavyAnalysisModule
from moybot.core.errors import ModuleNotImplementedError
from moybot.core.model.candidate import Candidate
from moybot.core.model.features import Feature, FeatureSet

__all__ = [
    "SPEC_CATEGORIES",
    "DeclaredOnlyModule",
    "HeavyAnalysisRegistry",
    "spec_category_modules",
]

SPEC_CATEGORIES: Final[tuple[str, ...]] = (
    "cluster_graph_analysis",
    "funding_source_analysis",
    "wallet_relationship_analysis",
    "influencer_correlation",
    "wash_trading_detection",
    "contract_analysis",
    "historical_behavior",
    "social_signals",
)
"""The heavy-analysis categories listed in PROJECT_SPEC.md §3."""


@final
class DeclaredOnlyModule:
    """A declared but unimplemented heavy-analysis category."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def analyze(self, candidate: Candidate) -> tuple[Feature, ...]:
        del candidate
        msg = (
            f"heavy-analysis module {self._name!r} is declared but not implemented in Phase 1; "
            "its methodology is an OPEN QUESTION (PROJECT_SPEC.md §3, §9)"
        )
        raise ModuleNotImplementedError(msg)


def spec_category_modules() -> tuple[HeavyAnalysisModule, ...]:
    """Instantiate one declared-only module per PROJECT_SPEC.md §3 category."""
    return tuple(DeclaredOnlyModule(name) for name in SPEC_CATEGORIES)


@final
class HeavyAnalysisRegistry:
    """Holds all known modules and runs only those explicitly enabled."""

    def __init__(
        self,
        modules: Sequence[HeavyAnalysisModule],
        enabled: Iterable[str] = (),
    ) -> None:
        self._modules = {module.name: module for module in modules}
        enabled_names = tuple(enabled)
        unknown = sorted(set(enabled_names) - set(self._modules))
        if unknown:
            msg = f"unknown heavy-analysis modules enabled: {', '.join(unknown)}"
            raise ValueError(msg)
        self._enabled = enabled_names

    @property
    def available(self) -> tuple[str, ...]:
        return tuple(self._modules)

    @property
    def enabled(self) -> tuple[str, ...]:
        return self._enabled

    def analyze(self, candidate: Candidate) -> FeatureSet:
        """Run every enabled module and collect its features."""
        features: list[Feature] = []
        for name in self._enabled:
            features.extend(self._modules[name].analyze(candidate))
        return FeatureSet(features=tuple(features))
