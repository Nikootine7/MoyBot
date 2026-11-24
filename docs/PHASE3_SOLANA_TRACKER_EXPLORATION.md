# Phase 3 exploratory audit: Solana Tracker

**Status: EXPLORATORY.** This records a read-only capability check through the connected ChatGPT plugin. It does not select Solana Tracker as MoyBot's production provider, define Smart Wallet, add thresholds, or authorize network code in the repository.

**Checked:** 2026-11-24

## What the connected tools returned

- Memecoin market statistics returned current aggregate activity.
- Seven-day trader and KOL leaderboards returned wallet addresses and provider-reported performance fields, so they can supply analyst-reviewed seed candidates.
- For one general leaderboard wallet, the wallet summary, positions, and recent-trade calls returned data. The summary includes realized and unrealized PnL, invested/proceeds, ROI, win rate, trade counts, average holding time, and an ROI distribution. Position rows include mint, PnL, holdings, trade counts, and first/last trade times. Recent-trade rows include token amounts, USD volume, venue, timestamp, and transaction signature.
- The service-status tool reported all six listed components operational and no active incidents. The separate network-status call returned 403 Forbidden. That is an endpoint-specific access failure in this check, not evidence that the provider's services were down.

## Data-quality and coverage observations

- Leaderboard and wallet-summary metrics are not interchangeable as exposed. For the sampled wallet, the leaderboard's period win-rate field was 100%, while the wallet summary returned 61.36% win rate and 62.5% token win rate. The periods and definitions are not sufficiently aligned to combine these into one score.
- A sampled position reported $207,295.96 realized PnL with zero buys, zero invested, two sells, and null ROI. This cannot be treated as a verified net return with a known cost basis.
- The connected plugin wrapper's recent-trade call exposes a timestamp and signature but no slot or first-observed time, and accepts a result limit without a page cursor. This is a wrapper limitation; the underlying product API is broader, as documented below.
- A KOL present in the leaderboard returned null fields in the wallet PnL summary and no rows from positions or recent trades. Leaderboard coverage therefore does not guarantee wallet-level history coverage.
- Parsing one recent transaction signature failed because the RPC client reported transaction version 1 unsupported and requested maxSupportedTransactionVersion=1. The connected transaction tool exposes no parameter for that setting, so raw transaction verification was unavailable for that sample.

These observations are from a small live capability check, not a representative coverage study. Wallets and metrics surfaced by a leaderboard are provider-selected and subject to winner-selection bias.

## Underlying product API documented beyond the plugin wrapper

The official [Wallet Trades API V2](https://docs.solanatracker.io/data-api/trades-v2/wallet/get-wallet-trades) documents a paginated REST history route. It supports cursor-based pages (up to 500 trades per page), time bounds, and ascending or descending order. Full trade records include transaction signature, slot, transaction and swap indices, token and quote legs, raw amount strings, owner balance changes, fees and tips, route, venue, and pool. The API requires an x-api-key header; its lighter basic mode omits several accounting fields.

The official [Wallet Trades V2 Datastream](https://docs.solanatracker.io/datastream/websockets/wallettradesv2) documents a live wallet room carrying the V2 trade format; its page says to load history from REST. The [connection guide](https://docs.solanatracker.io/guides/datastream-protocol) says Datastream requires a Data API key and a Premium, Business, or Enterprise plan. It documents a 100,000-room limit per connection and closes a connection that falls more than 1 MiB behind. Reconnecting and rejoining is documented; a reconnect/backfill procedure still needs to be designed and validated. The reviewed pages do not establish a latency SLA or historical-retention bound, and pricing was not evaluated.

KOL and whale streams are also documented, but they represent provider-defined cohorts (tracked KOL labels or USD-size tiers). They can provide candidate seeds, not MoyBot's final Smart Wallet definition. Token-wide streams require a mint to subscribe to, so they do not by themselves solve discovery across an unknown token universe.

## Plan and service terms (checked 2026-11-24)

The [official pricing and limits page](https://docs.solanatracker.io/pricing) confirms Datastream is plan-gated and requires a separate Data API key. The connected ChatGPT plugin does not provide MoyBot with that key or a subscription. Current quotas and plan eligibility must be checked on the official page before any provider decision.

The [Terms of Service](https://www.solanatracker.io/terms), last updated 2026-03-23, disclaim guarantees of uptime, latency, continuous availability, and data accuracy/completeness. They require compliance with applicable sanctions and export-control laws and say paid subscriptions may be processed through Stripe or Helio. The reviewed public terms do not name Iran or confirm regional/payment eligibility. Access from Iran therefore remains unverified; do not assume an API subscription can be opened or paid for.

## What this supports for MoyBot

The connected plugin is useful for manual candidate discovery and schema reconnaissance. The underlying Solana Tracker products are a promising source to evaluate further because their documented REST and WebSocket interfaces expose fields that the plugin wrapper omits, including chain ordering and full trade accounting.

That is not yet a production-provider decision. Access requires a separate API key and eligible Datastream subscription; service quality, latency, historical coverage, reconnect/backfill behavior, endpoint metric definitions, and follower-execution accounting remain to be validated. Keep the repository offline under D-004 until a provider decision is explicitly made. Do not use leaderboard rows as approved Smart Wallets, training labels, or production signals.

The Smart Wallet definition and venue universe remain open. No candidate-wallet list or historical export has been supplied; provider leaderboards are source-selected seeds, not a representative evaluation universe.

## Next research step

Compare candidate sources against a provider-neutral inventory: trade identity and ordering (slot/signature), provider first-seen time, amount units and cost basis, historical depth and pagination, venue coverage, error behavior, freshness/latency evidence, reconnection and backfill, and the information needed to estimate a follower's net return. Preserve missing or unsupported fields as unknown rather than zero. Only make a provider or ingestion decision after that comparison.
