"""Configuration.

No undecided domain value may acquire a default (PROJECT_SPEC.md §9, §10.3).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from moybot.app.config import AppConfig, load_config

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_defaults_configure_no_domain_value() -> None:
    config = AppConfig()
    assert config.strategies.bot_a.score_threshold is None
    assert config.strategies.bot_b.score_threshold is None
    assert config.strategies.bot_a.weights is None
    assert config.strategies.bot_b.weights is None
    assert config.validation.staleness is None
    assert config.validation.deterioration is None
    assert config.heavy_analysis.enabled_modules == ()


def test_defaults_configure_operational_values() -> None:
    config = AppConfig()
    assert config.storage.data_dir == Path("./.moybot-data")
    assert config.logging.level == "INFO"


def test_missing_config_path_yields_defaults() -> None:
    assert load_config(None) == AppConfig()


def test_example_config_leaves_every_domain_value_undecided() -> None:
    config = load_config(REPO_ROOT / "config" / "pipeline.example.toml")
    assert config.strategies.bot_a.enabled
    assert config.strategies.bot_b.enabled
    assert config.strategies.bot_a.score_threshold is None
    assert config.validation.staleness is None
    assert config.validation.deterioration is None


def test_configured_values_are_loaded(tmp_path: Path) -> None:
    path = tmp_path / "pipeline.toml"
    path.write_text(
        """
[strategies.bot_a]
score_threshold = "1.5"

[strategies.bot_a.weights]
some_feature = "0.25"

[validation.staleness]
max_snapshot_age_ms = 750
max_slot_lag = 3
""",
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.strategies.bot_a.score_threshold == Decimal("1.5")
    assert config.strategies.bot_a.weights == {"some_feature": Decimal("0.25")}
    assert config.validation.staleness is not None
    assert config.validation.staleness.max_slot_lag == 3


def test_partial_staleness_section_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "pipeline.toml"
    path.write_text("[validation.staleness]\nmax_slot_lag = 3\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_config(path)


def test_unknown_config_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "pipeline.toml"
    path.write_text("[storage]\nunexpected = 1\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_config(path)
