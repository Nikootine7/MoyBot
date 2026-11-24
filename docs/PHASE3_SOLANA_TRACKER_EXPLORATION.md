# Phase 3 exploratory audit: Solana Tracker

**Status: EXPLORATORY.** This records a read-only capability check through the connected ChatGPT plugin. It does not select Solana Tracker as MoyBot's production provider, define Smart Wallet, add thresholds, or authorize network code in the repository.

**Checked:** 2026-11-24

## What the connected tools returned

- Memecoin market statistics returned current aggregate activity.
- Seven-day trader and KOL leaderboards returned wallet addresses and provider-reported performance fields, so they can supply analyst-reviewed seed candidates.
- For one general leaderboard wallet, the wallet summary, positions, and recent-trade calls returned data. The summary includes realized and unrealized PnL, invested/proceeds, ROI, win rate, trade counts, average holding time, and an ROI distribution. Position rows include mint, PnL, holdings, trade counts, and first/last trade times. Recent-trade rows include token amounts, USD volume, venue, timestamp, and transaction signature.
- The service-status tool reported all six listed components operational and no active incidents. The separate network-status call returned 403 Forbidden. That is an endpoint-specific access failure in this check, not evidence that the provider's services were down.

## Additional bounded venue and launch probe

A second read-only check on 2026-11-24 used the 1-hour market-statistics view and the launchpad listing tools:

- Market statistics returned 15 market buckets, including an all-market aggregate and provider-defined venue and rollup rows. The sample contains parent/aggregate labels such as Raydium (All) and Meteora (All) alongside more specific Raydium and Meteora buckets. Do not sum aggregate and component rows as if they were disjoint.
- The `stage=new` call returned five token rows. The rows included a source-reported market label and launchpad-curve percentage, but no pool ID, transaction signature, slot, or source first-seen timestamp. All five rows in this small sample carried the Pumpfun label; this does not establish complete or exclusive launchpad coverage.
- The `stage=graduating` call returned five rows labelled `meteora-curve` with a source-reported `launchpadCurvePct`. They had no pool ID, signature, slot, or source first-seen time, so the provider's stage label is not itself proof that an on-chain migration occurred.
- The `stage=graduated` call returned HTTP 403 from the connected plugin endpoint. The earlier service-status result reported the listed service components operational, so this is an endpoint/tool-level access failure in this sample, not evidence of a provider-wide outage. Graduation-stage coverage remains unknown.

A recheck on 2026-11-24 first returned 403 Forbidden for `stage=new` (`limit=10`), but subsequent `stage=new` (`limit=5`) and `stage=graduated` (`limit=5`) requests succeeded. The successful `new` page contained five rows, all labelled `pumpfun`; the `graduated` page contained five rows labelled `meteora-dyn-v2` (three) or `pumpfun-amm` (two). A separate successful `stage=graduating` page contained five rows labelled `meteora-curve`. The returned wrapper objects included `createdAt` but no separate pool ID, transaction signature, or slot; these samples do not establish `createdAt` as source-first-seen time. The status endpoint reported all six listed components operational and no active incidents. The initial 403 was therefore intermittent endpoint/tool behavior, not evidence of a provider-wide outage or of continuous endpoint health.

A parallel bounded Nova `new_pairs` page and Tracker `stage=new` page each returned five rows and overlapped on two mints, with three unmatched rows per page. Nova provenance names Solana Tracker as the upstream provider, so this is a consistency check across wrappers, not independent corroboration. One shared mint was named `Loneliness` by Nova and `Unknown` by Tracker. The pages are bounded observations with no independent reference; do not interpret their 2/5 overlap as recall or completeness.

These bounded outputs are useful for schema reconnaissance only. They do not establish venue completeness, disjoint market buckets, or an on-chain event ledger.

## Data-quality and coverage observations

- Leaderboard and wallet-summary metrics are not interchangeable as exposed. For the sampled wallet, the leaderboard's period win-rate field was 100%, while the wallet summary returned 61.36% win rate and 62.5% token win rate. The periods and definitions are not sufficiently aligned to combine these into one score.
- A sampled position reported $207,295.96 realized PnL with zero buys, zero invested, two sells, and null ROI. This cannot be treated as a verified net return with a known cost basis.
- The connected plugin wrapper's recent-trade call exposes a timestamp and signature but no slot or first-observed time, and accepts a result limit without a page cursor. This is a wrapper limitation; the underlying product API is broader, as documented below.
- A KOL present in the leaderboard returned null fields in the wallet PnL summary and no rows from positions or recent trades. Leaderboard coverage therefore does not guarantee wallet-level history coverage.
- Parsing one recent transaction signature failed because the RPC client reported transaction version 1 unsupported and requested maxSupportedTransactionVersion=1. The connected transaction tool exposes no parameter for that setting, so raw transaction verification was unavailable for that sample.

These observations are from a small live capability check, not a representative coverage study. Wallets and metrics surfaced by a leaderboard are provider-selected and subject to winner-selection bias.

## Launchpad-listing API documented beyond the plugin wrapper

Official [New, Graduating and Graduated](https://docs.solanatracker.io/data-api/tokens/get-token-overview), [Graduating Tokens](https://docs.solanatracker.io/data-api/tokens/get-graduating-tokens), and [Graduated Tokens](https://docs.solanatracker.io/data-api/tokens/get-graduated-tokens) references describe these direct Data API routes:

- `GET /tokens/multi/all` returns latest, graduating, and graduated categories in one response. Its documented `limit` defaults to 100 and has a maximum of 500 per category; filters include creation-time bounds, market, liquidity, market cap, and risk score. No page or cursor parameter is listed.
- `GET /tokens/multi/graduating` lists graduating launchpad tokens (the documentation names Pump.fun, letsbonk.fun, and Jupiter Studio) and exposes `limit` plus curve, holder, creation-time, market, liquidity, and risk filters. No page or cursor parameter is listed.
- `GET /tokens/multi/graduated` documents a `page` parameter (default 1) and a `limit` (default 100, maximum 500), plus creation-time, market, liquidity, and risk filters.

The response schemas expose token creation fields (`creator`, `created_tx`, `created_time`) and pool fields including `poolId` and `market`. The schemas do not specify a source first-seen timestamp or explicit migration event signature and slot; an `events` object is listed without its subfields defined. A token's `created_tx` is under `token.creation`, so it must not be assumed to identify a later pool migration. These are documented direct-API fields, not fields verified in the ChatGPT plugin response. The Data API references require an `x-api-key`; no direct API call or account entitlement was tested, and D-004 remains in force.

## Liquidity history and stream coverage documented by the provider

The [Track Solana Liquidity Additions and Removals guide](https://docs.solanatracker.io/guides/liquidity) distinguishes the documented swap and liquidity paths:

- The Trades V2 pool endpoint (`GET /v2/trades/{token}/{pool}`) provides pool-scoped swaps with transaction signature, slot, transaction index, swap index, raw token amounts, fee details, program, route and cursor pagination. It is for a known token/pool and is not a pool-discovery feed.
- Liquidity additions/removals remain on legacy REST trade-history routes, including `events=all` and `events=liquidity`; the pool-specific route is marked deprecated for swaps, while the guide says liquidity events remain there. Pages use cursors and can contain `add_liquidity`/`remove_liquidity` rows with transaction signature, program/program ID, pool, wallet, time, slot, and exact amount strings.
- Datastream documents liquidity rooms by token, token/pool, token/pool/wallet, pool, or wallet, and requires a Premium, Business, or Enterprise plan. Live events are provisional at processed commitment; they can disappear on a fork and the guide says there is no rollback notification. REST history is confirmed/finalized and is the documented reconciliation path. Overlapping room subscriptions may duplicate actions; no internal event ID is exposed, and one transaction can contain multiple liquidity actions.
- Named supported instruction families include Raydium AMM v4/CPMM/CLMM, Orca Whirlpool, Pump AMM, Meteora DAMM v1/v2 and DLMM, Liquid Swap, and Futarchy. The guide excludes standalone fee/reward claims, LP-token mint/burn, rent, and unrelated transfers; coverage depends on instruction and available on-chain data.

This is a documented subset of liquidity activity, not proof of exhaustive venue/program coverage. The required liquidity history still depends on a legacy REST route, and stream recovery, latency, retention, and territory/account eligibility are unverified. These docs do not authorize a direct adapter; D-004 remains in force.

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

D-013 approves the initial broad offline research universe across Solana token launch and pool activity; Bot A/B production venue filters remain open. No candidate-wallet list or historical export has been supplied; provider leaderboards are source-selected seeds, not a representative evaluation universe.

## No-key pair lookup check

During this turn, a fresh bounded `stage=new` plugin page returned five rows. A direct DEX Screener public GET lookup for those five known mints, with no API key, returned one Solana pair for each. All five pair rows reported `dexId=pumpfun`, matching the Tracker page's source-reported `market=pumpfun`; each DEX `pairCreatedAt` also matched the corresponding Tracker `createdAt` to the second. This establishes that the no-key lookup worked for these five already-known mints in this session, not that the endpoint is a complete launch feed or that it detects first-seen time.

The response included pair addresses, base and quote token identities, transaction counts, volume, and pair creation time. It returned no `liquidity` object for any of the five. Two rows had no USD price and reported zero swaps/volume, while the Tracker page still showed nonzero quoted price/liquidity. At least two other price snapshots differed materially between the sources. The API response had no observation timestamp and the calls were not atomic; market movement or indexing timing cannot be separated from a source-data discrepancy. One pair used a non-SOL quote mint, reinforcing that quote mint must be preserved per pool.

Interpretation: the route is useful for looking up known pooled tokens and preserving pair-level context, but this sample does not qualify DEX Screener as a liquidity source, a pre-pool launch detector, or a substitute for raw event/history coverage. Preserve both source records and keep unexplained differences visible.

## Keyless GeckoTerminal latest-pools check

During this turn, a direct GET to `/api/v2/networks/solana/new_pools?include=base_token,quote_token,dex` returned 20 Solana pool records without an API key. The rows exposed pool addresses, `pool_created_at`, base/quote token identities, DEX labels, USD/native prices, FDV, transaction and volume windows, and `reserve_in_usd`. The bounded response included provider labels for Pump.fun, PumpSwap, Meteora DAMM V2, and Raydium LaunchLab. This shows the route can return cross-venue pool observations in one request; it does not establish exhaustive venue coverage or a first-seen/receive-time latency. It is a pool feed, so it does not cover a bonding-curve launch before a DEX pool exists; Bot B's pre-pool discovery remains unresolved.

All returned rows had `market_cap_usd=null`; several reserve/volume combinations were unusual, so these remain provider-reported values that need validation. The endpoint's response did not include a separate observation timestamp. The API is beta, and official pages conflict on its free request limit: the CoinGecko support answer updated 2026-11-23 says 30 calls/minute, while the product landing page describes 10 to 250 calls/minute. For planning, use the lower 10/minute figure until the live limit is confirmed. The same official licensing guidance says the free/keyless tier does not grant commercial-use rights; this route is only a personal/research candidate unless MoyBot's eventual use is licensed.

## Pre-pool raw-event candidate: public Solana RPC

Official Solana docs describe `logsSubscribe` over WebSocket and its `mentions` filter for a single address. A notification includes `context.slot`, transaction `signature`, `err`, and raw `logs`. The public mainnet WebSocket endpoint is `wss://api.mainnet.solana.com`. This is a no-key candidate for observing transactions involving one selected program or wallet address at a time; it is not a parsed launch/trade feed.

A runtime would still need per-program/per-wallet filters, transaction fetching and instruction decoding, source-receive timestamps, fork-aware handling, duplicate suppression, and gap reconciliation. Public RPC has shared limits and no production SLA; official docs list up to 100 requests/10 seconds per IP, 40 per single RPC, and 40 concurrent connections, with limits subject to change. No runtime query or code was added to the repository.

## Next research step

Compare candidate sources against a provider-neutral inventory: trade identity and ordering (slot/signature), provider first-seen time, amount units and cost basis, historical depth and pagination, venue coverage, error behavior, freshness/latency evidence, reconnection and backfill, and the information needed to estimate a follower's net return. Preserve missing or unsupported fields as unknown rather than zero. Only make a provider or ingestion decision after that comparison.
