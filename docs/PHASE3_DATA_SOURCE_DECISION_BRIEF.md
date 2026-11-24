# Phase 3: Data-source decision brief

**Status: RESEARCH / PROPOSED.** This brief compares the research tools available in ChatGPT with the direct data interfaces that a MoyBot runtime would require. It does not select a production provider, define production venue filters, define Smart Wallet, or authorize network code.

## Preserve the original system goal

The earlier project discussion confirms the intended principle: build the fastest bot that still has enough information to make a sound decision. Keep the pipeline event-driven and delta-first. A ChatGPT research result can help us inspect data, but it is not itself a continuous source adapter for that pipeline.

## Separate research access from runtime access

A connected ChatGPT plugin can run bounded, read-only queries inside ChatGPT. That does not give MoyBot code a provider SDK, credentials, persistent stream, predictable observation time, or service contract. The runtime must eventually use an explicitly selected direct source. Until then, keep the repository offline under D-004.

Current access status: You report that the Solana Tracker Data API key flow requires a €1 verification/authentication payment with cancel-anytime wording. That user-observed checkout requirement takes precedence over generic free-tier marketing for this account; no payment has been made, and we will not ask you to pay for it. The connected Solana Tracker ChatGPT plugin is working for bounded, read-only research without that API-key checkout. Plugin access is not a direct credential or runtime entitlement for MoyBot.

## Evidence gathered

### Solana Tracker

The connected research plugin returned market statistics, trader and KOL leaderboards, and wallet-level summary, position, and recent-trade responses. This supports analyst-led candidate discovery, but sampled results showed metric-scope differences and a position with no buys or invested basis despite reported realized PnL. One leaderboard-listed KOL had no wallet-level history in the plugin response. The detailed capability notes are in [the Solana Tracker exploration](PHASE3_SOLANA_TRACKER_EXPLORATION.md).

The underlying [Wallet Trades V2 REST API](https://docs.solanatracker.io/data-api/trades-v2/wallet/get-wallet-trades) documents cursor-paginated history, time bounds, slot/transaction/swap ordering, raw amount strings, balance changes, and fee fields. [Datastream](https://docs.solanatracker.io/datastream/websockets/wallettradesv2) documents live wallet-trade rooms with REST history for loading prior trades. This makes the direct product a technical source candidate; it does not establish delivery latency, completeness, or historical retention. The service terms disclaim uptime, latency, and data-accuracy guarantees. A separate API key and plan entitlement are required, and Iran-specific access remains unverified. The official [launchpad-token overview](https://docs.solanatracker.io/data-api/tokens/get-token-overview), [graduating-token](https://docs.solanatracker.io/data-api/tokens/get-graduating-tokens), and [graduated-token](https://docs.solanatracker.io/data-api/tokens/get-graduated-tokens) references document token-creation metadata and pool `poolId`/`market` fields. The graduated endpoint documents page-number pagination; the overview and graduating endpoints list result limits and filters but no page or cursor parameter. These schemas do not establish source first-seen time or a migration event's slot/signature. This is direct-API documentation, not evidence that the connected ChatGPT wrapper exposes those fields or that this account has API access.

The [liquidity guide](https://docs.solanatracker.io/guides/liquidity) documents pool swaps in Trades V2, but says liquidity adds/removes remain on legacy REST trade-history routes and separate Datastream liquidity rooms. Those live events are provisional at processed commitment, can disappear on a fork, and receive no rollback notice; confirmed REST history is the documented reconciliation path. The guide names several supported program families and explicit exclusions, so it is evidence of bounded instruction coverage, not exhaustive coverage of D-013's all-venue universe.

### Nova

A read-only Nova smart-money query succeeded and returned one bounded page of five screened observations with trade time, wallet, token, action, market, amounts, and transaction signature. The response did not supply an observation timestamp. **Source observation freshness is unknown.** The tool warning says the sample is screened/labelled and is not every profitable trader or whale. The capability description also says there is no standalone smart-money discovery endpoint and no durable watch subscription. This supports manual research and bounded snapshots, not MoyBot's continuous event feed or a complete evaluation dataset.

On 2026-11-24, a bounded Nova `new_pairs` request returned five rows, all with `source=pumpfun`. In a parallel bounded request, the Solana Tracker plugin's `stage=new` page also returned five rows; the pages overlapped on two mints, with three unmatched rows in each page. Nova's provenance reported Solana Tracker as the upstream provider, so this is a wrapper/source consistency observation, not independent coverage evidence or a recall estimate. For one shared mint, Nova supplied the name `Loneliness` while the Tracker wrapper returned `Unknown`, although the mint and `createdAt` matched. In the Nova page, every `pairAddress` equalled the token `address` and every `txHash` was null; the response did not establish a distinct pool ID or transaction signature. It supplied `blockTime`, `createdAt`, and `receivedAt`, but `observedAt` and `sourceFetchedAt` were null; status was `unknown`, and pagination metadata had `nextCursor=null` and `hasMore=null`. **Source observation freshness is unknown.** These bounded pages cannot establish all-venue coverage; missing pool and transaction identity remains unknown.

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

## Zero-euro route replacing the API-key checkout (research proposal)

The €1 Solana Tracker API-key checkout remains paused. The connected read-only plugin is the immediate route for analyst-led checks in ChatGPT; it does not provide MoyBot with a runtime credential or continuous feed.

### Better keyless candidate: GeckoTerminal latest pools

The [public API](https://api.geckoterminal.com/api/v2/networks/solana/new_pools?include=base_token%2Cquote_token%2Cdex) returned a live Solana `new_pools` page in this session without an API key. The response contained 20 pool records and reported pool address, creation time, base/quote tokens, DEX label, token prices, FDV, transactions, volume, and `reserve_in_usd`. The page included Pump.fun, PumpSwap, Meteora DAMM V2, and Raydium LaunchLab rows, so this is a stronger no-key candidate for cross-venue *pool* discovery and market enrichment than DEX Screener's known-token lookup. Because it lists pools, it cannot detect a bonding-curve launch before a DEX pool exists; Bot B's pre-pool discovery remains unresolved.

This is still only a bounded sample. It does not establish complete venue coverage, source-first-seen time, delivery latency, or an uptime/recovery guarantee. In the sample, `market_cap_usd` was null on the returned rows and some reserve/volume combinations looked unusual; retain raw values and validate them before using them as filters or ground truth. The API is in beta. CoinGecko's [support answer](https://support.coingecko.com/articles/6867086195-does-geckoterminal-have-an-api), updated 2026-11-23, says the public free API is limited to 30 calls/minute, while the [API landing page](https://www.geckoterminal.com/dex-api) says paid plans raise the limit from 10 to 250 calls/minute. Because these official pages conflict about the free limit, budget conservatively at 10 calls/minute until the current endpoint limit is confirmed.

CoinGecko's [licensing guidance](https://support.coingecko.com/articles/1043089972-what-are-the-differences-between-commercial-and-custom-licenses) says its free/keyless API does not grant commercial-use rights; paid access is required for a commercial product. Treat this as a personal/research candidate only unless the eventual product's licensing is cleared.

### DEX Screener and public RPC roles

DEX Screener remains an optional known-pair cross-check, not the primary discovery source. A no-key lookup returned a pair for all five Tracker mints in the prior sample, but omitted liquidity for all five; two rows had no USD price and zero swaps/volume, and at least two price snapshots differed materially. With no observation timestamps, the sample cannot establish which source was more current.

Solana's [public mainnet RPC](https://solana.com/docs/references/clusters) can complement the pool index with raw on-chain confirmation, but it is shared, rate-limited infrastructure and not intended for production. It does not provide indexed cross-venue pool enrichment, trade history, or recovery on its own; MoyBot would have to decode programs and handle gaps.

Recommended immediate route: continue manual research through the connected plugin; for a future no-cost *personal research prototype*, qualify GeckoTerminal's keyless latest-pools endpoint first, with RPC reserved for targeted raw-chain validation and DEX Screener as an optional pair cross-check. The source is a proposal, not a production selection or a change to D-004. Do not create another API account or pay for a key to continue the current research.

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

The offline research universe is approved. Use the already-connected read-only plugin for current manual research; no €1 API-key checkout is needed for that step. The no-key public RPC + DEX Screener route remains a candidate for qualification, not a selected production source. Follow [the source qualification plan](PHASE3_SOURCE_QUALIFICATION_PLAN.md), preserve missing fields as unknown, and keep D-004 in force until an explicit provider decision authorizes network code.
