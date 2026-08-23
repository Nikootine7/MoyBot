"""Continuously cached token state (PROJECT_SPEC.md §2.1).

Every field is optional and ``None`` means **unknown**, never zero. Unknown values are treated
as a risk by downstream validation (PROJECT_SPEC.md §10.8: stale data is a first-class risk),
which fails closed rather than assuming a value.

No threshold, weight or classification rule appears in this module. These types record what was
observed; deciding what an observation *means* is left to components that are configured
explicitly (see docs/DECISIONS.md D-006).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import final

from moybot.core.model.primitives import Pubkey, Slot, TimestampMs

__all__ = [
    "HolderDistribution",
    "LpState",
    "TokenMetrics",
    "TokenState",
    "TradeDirection",
    "WalletActivity",
    "WalletHistory",
]


class TradeDirection(StrEnum):
    """Direction of an observed wallet trade."""

    BUY = "buy"
    SELL = "sell"


@final
@dataclass(frozen=True, slots=True)
class TokenState:
    """Observed on-chain state of the mint account.

    These are raw account facts. Whether any combination of them constitutes a risk is an
    OPEN QUESTION (PROJECT_SPEC.md §9, rug-detection criteria) and is not decided here.
    """

    mint_authority: Pubkey | None = None
    freeze_authority: Pubkey | None = None
    update_authority: Pubkey | None = None
    supply: Decimal | None = None
    decimals: int | None = None


@final
@dataclass(frozen=True, slots=True)
class LpState:
    """Observed liquidity-pool state."""

    pool: Pubkey | None = None
    base_reserve: Decimal | None = None
    quote_reserve: Decimal | None = None
    lp_token_supply: Decimal | None = None
    lp_tokens_burned: Decimal | None = None


@final
@dataclass(frozen=True, slots=True)
class HolderDistribution:
    """Observed holder distribution.

    ``top_holder_shares`` is ordered descending; each entry is a fraction of supply in the range
    0-1. The number of entries reported is a property of the data source, not a requirement.
    """

    holder_count: int | None = None
    top_holder_shares: tuple[Decimal, ...] = ()


@final
@dataclass(frozen=True, slots=True)
class WalletActivity:
    """A single observed wallet trade on a token."""

    wallet: Pubkey
    mint: Pubkey
    direction: TradeDirection
    slot: Slot
    timestamp_ms: TimestampMs
    amount: Decimal | None = None


@final
@dataclass(frozen=True, slots=True)
class WalletHistory:
    """Observed history for one wallet (PROJECT_SPEC.md §2.1, "Wallet history").

    Phase 1 stores observations only. Wallet scoring and the Smart Wallet definition remain
    OPEN QUESTIONS (PROJECT_SPEC.md §9).
    """

    wallet: Pubkey
    activity: tuple[WalletActivity, ...] = ()
    first_seen_slot: Slot | None = None
    last_seen_slot: Slot | None = None


@final
@dataclass(frozen=True, slots=True)
class TokenMetrics:
    """Cached per-token state, one field per item of PROJECT_SPEC.md §2.1."""

    price: Decimal | None = None
    price_change: Decimal | None = None
    volume: Decimal | None = None
    buy_volume: Decimal | None = None
    sell_volume: Decimal | None = None
    liquidity: Decimal | None = None
    slippage_bps: Decimal | None = None
    holders: HolderDistribution = field(default_factory=HolderDistribution)
    dev_transaction_count: int | None = None
    dev_sold: bool | None = None
    smart_wallet_transaction_count: int | None = None
    smart_wallet_addresses: tuple[Pubkey, ...] = ()
    wallet_cluster_ids: tuple[str, ...] = ()
    token_state: TokenState = field(default_factory=TokenState)
    lp_state: LpState = field(default_factory=LpState)
