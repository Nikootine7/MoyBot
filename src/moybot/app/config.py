"""Configuration.

Every domain value that PROJECT_SPEC.md §9 leaves open — thresholds, weights, staleness limits,
deterioration limits — is optional here and has **no default**. Absent configuration makes the
affected component report "not configured" and fail closed; it never produces a substitute value.

Operational values that are not domain decisions (where to write data, log level) do have
defaults.
"""

from __future__ import annotations

import tomllib
from decimal import Decimal
from pathlib import Path
from typing import final

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AppConfig",
    "DeteriorationConfig",
    "HeavyAnalysisConfig",
    "LoggingConfig",
    "StalenessConfig",
    "StorageConfig",
    "StrategiesConfig",
    "StrategyConfig",
    "ValidationConfig",
    "load_config",
]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class StorageConfig(_StrictModel):
    """Where snapshots and provenance are written (docs/DECISIONS.md D-005)."""

    data_dir: Path = Path("./.moybot-data")


class LoggingConfig(_StrictModel):
    """Structured logging settings."""

    level: str = "INFO"


class HeavyAnalysisConfig(_StrictModel):
    """Which heavy-analysis modules to run (PROJECT_SPEC.md §3).

    Empty by default: every module is a declared-only stub in Phase 1, and enabling one is an
    error rather than a silent no-op.
    """

    enabled_modules: tuple[str, ...] = ()


class StrategyConfig(_StrictModel):
    """Per-strategy configuration.

    ``score_threshold`` and ``weights`` are intentionally absent by default. PROJECT_SPEC.md §9
    lists exact thresholds and weights as not final, so there is nothing to default them to.
    """

    enabled: bool = True
    score_threshold: Decimal | None = None
    weights: dict[str, Decimal] | None = None


class StrategiesConfig(_StrictModel):
    """Bot A and Bot B are configured separately (PROJECT_SPEC.md §7, §10.7)."""

    bot_a: StrategyConfig = Field(default_factory=StrategyConfig)
    bot_b: StrategyConfig = Field(default_factory=StrategyConfig)


class StalenessConfig(_StrictModel):
    """Staleness limits. Both values are required when this section is present."""

    max_snapshot_age_ms: int
    max_slot_lag: int


class DeteriorationConfig(_StrictModel):
    """Material-deterioration limits. All values are required when this section is present."""

    max_price_drop_fraction: Decimal
    max_liquidity_drop_fraction: Decimal
    max_slippage_bps: Decimal
    max_sell_pressure_ratio: Decimal
    cancel_on_dev_sold: bool
    cancel_on_smart_wallet_exit: bool
    cancel_on_lp_supply_change: bool


class ValidationConfig(_StrictModel):
    """Final pre-trade validation configuration (PROJECT_SPEC.md §5).

    With either section missing, validation cancels every candidate. That is deliberate: acting
    without a decided policy would mean inventing a risk limit.
    """

    staleness: StalenessConfig | None = None
    deterioration: DeteriorationConfig | None = None


@final
class AppConfig(_StrictModel):
    """Complete Phase 1 configuration."""

    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    heavy_analysis: HeavyAnalysisConfig = Field(default_factory=HeavyAnalysisConfig)
    strategies: StrategiesConfig = Field(default_factory=StrategiesConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)


def load_config(path: Path | None) -> AppConfig:
    """Load configuration from a TOML file, or return operational defaults."""
    if path is None:
        return AppConfig()
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    return AppConfig.model_validate(raw)
