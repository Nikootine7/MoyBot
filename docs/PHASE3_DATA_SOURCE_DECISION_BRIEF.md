# Phase 3: Data-source decision brief

**Status: RESEARCH / PROPOSED.** This brief compares the research tools available in ChatGPT with the direct data interfaces that a MoyBot runtime would require. It does not select a production provider, approve a venue universe, define Smart Wallet, or authorize network code.

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

## Fit against MoyBot's evidence needs

| Need | What current research access can establish | Remaining gap |
| --- | --- | --- |
| Candidate seeds | Public leaderboard, KOL, whale, and screened signal samples | Provider-defined selection is not a representative wallet universe |
| Event order | Direct Solana Tracker V2 docs describe slot, transaction index, and swap index | Plugin wrappers and the Nova sample do not establish this ordering end to end |
| Wallet track record | PnL summaries and positions exist in both research contexts | Metric definitions, cost basis, cohort coverage, and accounting treatment need reconciliation |
| Actionable event value | Recent trades and trade timestamps are visible | No validated first-observed latency, follower fill, or net-return replay |
| Continuous feed | Solana Tracker documents REST plus Datastream | Separate key/plan, reconnect and gap repair, and delivery behavior remain unvalidated |
| Historical evaluation | Some cursor-paginated pages are documented | No verified retention/completeness contract or representative labelled dataset |
| Venue context | Trade rows can identify venue/pool in the direct V2 product | The initial research universe has not been approved |

A provider-selected leaderboard must not become the only source of labels: that would measure how a curated ranking performs, not whether MoyBot can discover useful wallets from the intended universe.

## Proposed research scope

For the first offline comparison, I propose including Solana token launch and pool activity across venues while preserving launchpad, pool, and migration stage as separate labels. This follows the existing Solana-only scope and the prior Pump.fun/Jupiter/GMGN discussion, while letting Bot A's confirmation evidence and Bot B's early-event evidence be evaluated separately. It is a proposal only; it does not narrow or finalize either bot's production universe.

## Next decision gate

Before adding any live adapter, the project owner should confirm or edit that broad research scope. Then compare direct sources on history coverage, chain ordering, first-observed time, pagination/backfill, raw amount and fee semantics, venue coverage, data quality, service limits, and legal/account eligibility. Keep missing fields as unknown. Record a provider decision in the decision log before implementing network code.
