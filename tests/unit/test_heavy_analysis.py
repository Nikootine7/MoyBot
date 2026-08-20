"""Heavy-analysis registry and stubs."""

from __future__ import annotations

from decimal import Decimal

import pytest

from moybot.core.analysis.registry import (
    SPEC_CATEGORIES,
    HeavyAnalysisRegistry,
    spec_category_modules,
)
from moybot.core.errors import ModuleNotImplementedError
from tests.support import StubAnalysisModule, candidate


def test_all_spec_categories_are_registered() -> None:
    registry = HeavyAnalysisRegistry(spec_category_modules())
    assert registry.available == SPEC_CATEGORIES


def test_nothing_is_enabled_by_default() -> None:
    registry = HeavyAnalysisRegistry(spec_category_modules())
    assert registry.enabled == ()
    assert registry.analyze(candidate()).features == ()


@pytest.mark.parametrize("category", SPEC_CATEGORIES)
def test_enabling_a_spec_category_raises_rather_than_fabricating(category: str) -> None:
    registry = HeavyAnalysisRegistry(spec_category_modules(), enabled=[category])
    with pytest.raises(ModuleNotImplementedError, match="declared but not implemented"):
        registry.analyze(candidate())


def test_unknown_module_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown heavy-analysis modules"):
        HeavyAnalysisRegistry(spec_category_modules(), enabled=["not_a_module"])


def test_enabled_module_features_are_collected() -> None:
    module = StubAnalysisModule("stub", "stub_feature", Decimal("0.5"))
    registry = HeavyAnalysisRegistry([module], enabled=["stub"])
    features = registry.analyze(candidate())
    assert features.names() == ("stub_feature",)
