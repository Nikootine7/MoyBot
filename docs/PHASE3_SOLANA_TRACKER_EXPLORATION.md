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
- The wallet-level recent-trade response exposes a timestamp and signature, but no slot or first-observed time. The wrapper accepts a result limit but exposes no page cursor for this call, so it is not a demonstrated complete history feed.
- A KOL present in the leaderboard returned null fields in the wallet PnL summary and no rows from positions or recent trades. Leaderboard coverage therefore does not guarantee wallet-level history coverage.
- Parsing one recent transaction signature failed because the RPC client reported transaction version 1 unsupported and requested maxSupportedTransactionVersion=1. The connected transaction tool exposes no parameter for that setting, so raw transaction verification was unavailable for that sample.

These observations are from a small live capability check, not a representative coverage study. Wallets and metrics surfaced by a leaderboard are provider-selected and subject to winner-selection bias.

## What this supports for MoyBot

The plugin is useful for manual candidate discovery and for learning which fields a future source adapter would need to reconcile. It does not demonstrate the continuous event feed, slot-ordered history, completeness, first-seen latency, or follower-execution accounting needed to validate a production provider. It cannot establish a wallet's signal value at MoyBot's observation time.

Keep the repository offline under D-004. Do not use these leaderboard rows as approved Smart Wallets, training labels, or production signals. The Smart Wallet definition and venue universe remain open; the user has not supplied a wallet list or historical export.

## Next research step

Compare candidate sources against a provider-neutral inventory: trade identity and ordering (slot/signature), provider first-seen time, amount units and cost basis, historical depth and pagination, venue coverage, error behavior, freshness/latency evidence, and the information needed to estimate a follower's net return. Preserve missing or unsupported fields as unknown rather than zero. Only make a provider or ingestion decision after that comparison.
