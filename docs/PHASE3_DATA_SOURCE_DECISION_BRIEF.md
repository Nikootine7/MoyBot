# Phase 3: Data-source decision brief

**Status: RESEARCH / PROPOSED.** This brief compares the research tools available in ChatGPT with the direct data interfaces that a MoyBot runtime would require. It does not select a production provider, define production venue filters, define Smart Wallet, or authorize network code.

## Preserve the original system goal

The earlier project discussion confirms the intended principle: build the fastest bot that still has enough information to make a sound decision. Keep the pipeline event-driven and delta-first. A ChatGPT research result can help us inspect data, but it is not itself a continuous source adapter for that pipeline.

## Separate research access from runtime access

A connected ChatGPT plugin can run bounded, read-only queries inside ChatGPT. That does not give MoyBot code a provider SDK, credentials, persistent stream, predictable observation time, or service contract. The runtime must eventually use an explicitly selected direct source. Until then, keep the repository offline under D-004.

## Evidence gathered

### Solana Tracker

The connected research plugin returned market statistics, trader and KOL leaderboards, and wallet-level summary, position, and recent-trade responses. This supports analyst-led candidate discovery, but sampled results showed metric-scope differences and a position with no buys or invested basis despite reported realized PnL. One leaderboard-listed KOL had no wallet-level history in the plugin response. The detailed capability notes are in [the Solana Tracker exploration](PHASE3_SOLANA_TRACKER_EXPLORATION.md).

The underlying [Wallet Trades V2 REST API](https://docs.solanatracker.io/data-api/trades-v2/wallet/get-wallet-trades) documents cursor-paginated history, time bounds, slot/transaction/swap ordering, raw amount strings, balance changes, and fee fields. [Datastream](https://docs.solanatracker.io/datastream/websockets/wallettradesv2) documents live wallet-trade rooms with REST history for loading prior trades. This makes the direct product a technical source candidate; it does not establish delivery latency, completeness, or historical retention. The service terms disclaim uptime, latency, and data-accuracy guarantees. A separate API key and plan entitlement are required, and Iran-specific access remains unverified.

### Nova

A read-only Nova smart-money query succeeded and returned one bounded page of five screened observations with trade time, wallet, token, action, market, amounts, and transaction signature. The response did not supply an observation timestamp. **Source observation freshness is unknown.** The tool warning says the sample is screened/labelled and is not every profitable trader or whale. The capability description also says there is no standalone smart-money discovery endpoint and no durable watch subscription. This supports manual research and bounded snapshots, not MoyBot's continuous event feed or a complete evaluation dataset.

### Birdeye

The official [new-listing API](https://data.birdeye.so/docs/data-api/tokenmarket-list/get-defi-v2-tokens-new-listing) supports Solana and returns provider-reported newly listed tokens. The endpoint allows up to 20 items per request; its Solana-specific `meme_platform_enabled` option covers meme-platform-aware discovery where supported, and its docs recommend frequent polling and deduplication. Birdeye also documents [New Token Listing](https://data.birdeye.so/docs/websockets/new-token-listing.md) and [New Pair](https://data.birdeye.so/docs/websockets/new-pair.md) WebSocket subscriptions. These are relevant to the approved launch-and-pool universe, but public docs do not establish exhaustive coverage or a guaranteed first-seen time.

The [all-market list](https://data.birdeye.so/docs/data-api/tokenmarket-list/get-defi-v2-markets) is queried by a known mint and returns markets/pools for that token, with up to 20 results per page. It helps preserve venue and pool context after discovery; it is not an independent all-pool census.

Birdeye's [Transactions API](https://data.birdeye.so/docs/data-api/transactions) documents recent and filtered chain-wide V3 trade feeds, time-bounded token/pair/wallet history, and token-level trade filters. V3 Solana trade examples include transaction hash, block number and time, instruction indexes, owner/signers, source, pool ID, and raw amount strings. This is a comparatively rich normalized event shape for cross-venue research. The legacy token-trades page has an internal pagination-bound discrepancy (50,000 in a usage note versus 10,000 in the parameter reference), so bounds must be confirmed against the selected V3 endpoint rather than inferred from the legacy endpoint.

### Helius

[LaserStream](https://www.helius.dev/laserstream) and its Yellowstone-compatible transaction/account filters provide lower-level event inputs for a multi-venue decoder. [Parsed Streams](https://www.helius.dev/docs/parsed-streams) and the [Parsed Events API](https://www.helius.dev/blog/parsed-events-and-streams) apply an IDL catalogue with raw fallbacks, but Helius documents these parsed products as open beta. This reduces decoding work for covered programs; it does not prove that every launchpad, pool program, route, and migration is decoded. Otherwise MoyBot would own and maintain those decoders.

[Historical replay](https://www.helius.dev/docs/laserstream/historical-replay) is a stream-recovery window of about 48 hours, not long-term backfill; older replayed data is finalized-only. For history, [getTransactionsForAddress](https://www.helius.dev/docs/rpc/gettransactionsforaddress) paginates by address, but each address is queried separately and the docs describe special routing and slot-scan fallback cases. Helius therefore offers flexible raw visibility, with more ingestion/decoder work and no turnkey complete cross-venue trade ledger.

### Account and regional eligibility

The current [Helius Cloud Services Agreement](https://www.helius.dev/terms) limits service use to business purposes, prohibits personal/household/familial use, and requires the customer to represent that it is not ordinarily resident in a jurisdiction under comprehensive U.S. sanctions. Since this project has been treated as an individual project and you have previously said your residence is Iran, Helius eligibility is not cleared by the current documents; OFAC maintains an [Iran sanctions program](https://ofac.treasury.gov/sanctions-programs-and-country-information/iran-sanctions), while Helius's exact account eligibility still requires confirmation from the provider. This is a contract-based concern, not a legal determination. A VPN endpoint does not change the residence representation.

Birdeye's [public Terms of Service](https://birdeye.so/data-api/terms-of-service), last updated 2025-04-11, require lawful use and accurate account information and restrict redistribution of its service/data. The reviewed public text does not give a clear Iran-specific access confirmation. Solana Tracker's Iran-specific eligibility also remains unverified. Treat access and any public/commercial reuse as unresolved for all three until the applicable account terms are confirmed.

## Fit against MoyBot's evidence needs

| Need | What current research access can establish | Remaining gap |
| --- | --- | --- |
| Candidate seeds | Solana Tracker launch/leaderboard views; Birdeye new-listing/new-pair feeds; bounded Nova samples | Provider indexes and curated cohorts may omit activity; no representative universe has been measured |
| Event order | Solana Tracker V2 documents slot, transaction index, and swap index; Birdeye V3 documents block number/time and instruction indexes; Helius exposes transaction streams | No cross-provider order reconciliation or complete same-slot ordering has been validated |
| Wallet track record | Solana Tracker and Nova expose wallet-level summaries/positions; Birdeye documents wallet trade history and PnL endpoints | Accounting definitions, cost basis, missing history, and cohort coverage need reconciliation |
| Actionable event value | Birdeye and Helius document live feeds; Solana Tracker documents wallet-trade streaming | No comparable source-first-seen latency, MoyBot receive-time sample, or follower-fill replay exists |
| Continuous feed | Solana Tracker Datastream; Birdeye listing, pair, and wallet WebSockets; Helius LaserStream/Parsed Streams | Reconnect/gap behavior, entitlements, and data loss are not validated in MoyBot |
| Historical evaluation | Cursor/paginated wallet history at Solana Tracker; Birdeye V3 recent/archive and time-bounded trade endpoints; Helius per-address history | Retention and completeness guarantees are unverified; Helius stream replay alone covers only about 48 hours |
| Venue context | Birdeye returns source/pool labels; Solana Tracker returns platform/pool fields; Helius gives program/account instructions for decoding | Provider labels, on-chain programs, pool IDs, and migration stages must remain separate; none proves universal venue coverage |
| Account and territory | Public terms reveal explicit Helius use/residence conditions; Birdeye and Solana Tracker still need account-specific eligibility confirmation | VPN location does not establish contractual eligibility; no account/API access was tested |

A provider-selected leaderboard must not become the only source of labels: that would measure how a curated ranking performs, not whether MoyBot can discover useful wallets from the intended universe.

## Approved initial research scope

D-013, approved 2026-11-24, sets the first offline research and evaluation universe to Solana token launch and pool activity across venues. Preserve source-reported venue/program, pool, and migration-stage labels separately, and keep missing labels unknown. This follows the existing Solana-only scope and prior Pump.fun/Jupiter/GMGN discussion, while letting Bot A's confirmation evidence and Bot B's early-event evidence be evaluated separately. D-013 does not set either bot's production venue filters.

## Proposed normalized trade observation

This is a provider-neutral schema proposal for comparing sources, not an approved domain contract or wallet score.

| Field group | Preserve | Why |
| --- | --- | --- |
| Event identity and order | Solana signature, token mint, wallet, owner and fee payer separately; slot, transaction index, swap index | Deduplicate events and order same-slot swaps without treating a payer as the token-balance owner |
| Event time | Chain event time, source first-seen time, and MoyBot receive time as separate nullable values | Measure how late the signal becomes actionable; a missing observation time stays unknown |
| Swap amounts | Token and quote mints, raw amount strings, decimals, prices, and any reported USD notional | Preserve exact units and avoid using rounded provider PnL as the underlying ledger |
| Costs and route | Network/priority fees, tips, platform fee plus fee mint, program, platform, pools, and route | Estimate net return and distinguish the on-chain program from the user-facing trading app |
| Source coverage | Endpoint/schema version, page cursor, pagination state, partial/sampled warnings, and missing-field notes | Make history gaps and source limitations visible in replay and provenance |

The Solana Tracker V2 wallet-trade documentation exposes most of these trade fields, but not a guaranteed source first-seen time or an availability/completeness contract. In the Nova sample, chain ordering and observed-at time were absent. **Source observation freshness is unknown.**

Unknown values remain null, not zero. A provider's PnL summary can help investigate a wallet, but trade-level cost basis, fees, and event timing must be assessed separately. Keep wallet track record and the value of one actionable event as separate evaluations. Do not add a Smart Wallet threshold, weights, or a live event detector here.

## Next decision gate

The offline research universe is approved. A source-neutral capture and comparison procedure is in [the qualification plan](PHASE3_SOURCE_QUALIFICATION_PLAN.md). It requires a same-window evidence sample, an independent reference before making completeness claims, and account/territory eligibility before provider access. Keep missing fields as unknown, and record a provider decision in the decision log before implementing network code.
