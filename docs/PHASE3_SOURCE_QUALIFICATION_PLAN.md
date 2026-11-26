# Phase 3: Source qualification plan

**Status: PROPOSED / RESEARCH PLAN.** This document describes how to compare data sources against D-013 and the proposed normalized trade observation. It does not select a provider, define a production API contract, set bot rules, or introduce latency, completeness, or scoring thresholds.

## Gate 0 — account and access eligibility

Before repeated provider access, record the provider legal entity, current terms version, territory/account eligibility, permitted use, restrictions on reuse or redistribution, and applicable data entitlements. This also applies to keyless public endpoints: review the free tier's license and rate limit before using it as a continuing source. A VPN exit location does not establish ordinary residence or contractual eligibility. If the terms or provider response do not clear eligibility, mark that source blocked or unknown rather than attempting access.

Current findings (2026-11-26): GeckoTerminal terms require users not to reside, be domiciled in, or access from a listed excluded country; CoinGecko’s current list includes Iran. PumpPortal prohibits interaction with wallets located in, established in, or resident in Iran and expressly prohibits VPN/IP circumvention of that restriction. Mark wallet-linked trade streams blocked where the associated wallet is in a prohibited locality; the public terms do not clearly resolve read-only launch/migration stream eligibility, so keep those blocked pending written clarification. DEX Screener’s general terms require the user to represent that they are not located in a country subject to a U.S. government embargo; OFAC describes Iran as subject to broad jurisdiction-based sanctions. Mark DEX Screener blocked pending provider clarification and do not repeat the earlier bounded lookup. These are provider-term findings, not a legal determination. See the [DEX Screener terms](https://docs.dexscreener.com/privacy/terms-and-conditions) and [OFAC FAQ 10](https://ofac.treasury.gov/faqs/10).

Keep D-004 in force: this plan introduces no runtime provider adapter, persistent direct-provider queries, API key, network code, or execution path. Bounded read-only research queries used to evaluate a source are evidence only and are not part of MoyBot's runtime. Store any future credentials only in a user-controlled secret store; never place them in the repository or a fixture.

## Gate 1 — freeze a comparison capture

Once eligible access and an explicit provider decision exist:

- Select a bounded Solana slot interval that all compared sources can query or stream. Store the exact start/end slots, query parameters, source versions, capture start/end times, and pagination state in a manifest. The interval is a study input, not a product constant.
- Use an independent transaction/block reference for the same interval if one is available and authorized. Without that reference, report source overlap only; do not claim completeness or recall.
- Preserve raw responses and source provenance before normalization. Record response time at MoyBot, source-provided observation time when present, and chain event time separately.
- Include each observed event family in D-013: token launches/listings, pool creation, swaps, liquidity additions/removals, and migration-stage changes where the source or reference reports them. These are evaluation categories, not production detectors.
- Preserve source-reported venue, on-chain program, pool, and migration-stage labels as separate nullable fields. Do not infer one from another; missing remains unknown.
- Keep transaction identity separate from swap identity. Preserve signatures, slot/block, outer and inner instruction indexes, and provider swap indexes when supplied. A transaction may contain multiple routes or swaps; do not deduplicate by signature alone.
- Keep owner, signer, fee payer, token-balance owner, and trader attribution separate when the source exposes them. Do not assign a fee payer as the token owner by default.
- Keep token and quote raw amount strings, mint addresses, decimals, fees, and fee mints. Do not reconstruct raw quantities from rounded UI amounts.

## Gate 2 — compare observable behavior

| Dimension | Record and compare | Required interpretation |
| --- | --- | --- |
| Launch and pool coverage | Events by event family, venue/program label, pool, and slot against the independent reference | If no independent reference exists, state that completeness is unknown |
| Event identity and ordering | Signature, slot/block number, transaction order, instruction indexes, swap index, and source cursor | Preserve multiple swaps in one transaction; unknown order fields stay unknown |
| Cross-venue labels | Source-reported venue/platform, program ID, pool ID, route, and migration stage | Store each label separately and retain the source that supplied it |
| Wallet attribution | Owner, signer, fee payer, token account owner, and source trader field | Differences are evidence to reconcile, not fields to collapse |
| Amounts and costs | Raw token/quote values, decimals, fee amount and mint, and source UI amount | Reconcile unit semantics and transaction-level versus swap-level fees before calculating net return |
| Time and actionability | Chain event time, source first-seen time if supplied, local receipt time, and slot | Report observed lag distributions; do not infer a provider timestamp from local receipt |
| History and pagination | Request bounds, cursor/offset, page boundaries, repeats, missing pages, errors, and endpoint limits | A completed pagination loop is not proof of retained or complete history |
| Stream recovery | Per-address checkpoint, interruption boundary, replay/backfill result, duplicates, and gaps | Public logs have no documented replay cursor; use paginated `getSignaturesForAddress` (max 1,000/request) as a recovery attempt, not a completeness guarantee |
| Public WebSocket capture | One program/wallet address per `logsSubscribe` mentions filter, commitment, slot/signature/logs, local receive time, subscription count and reconnect gaps | Logs are raw; the filter holds one address, decoding and recovery are MoyBot responsibilities, and public RPC is not production infrastructure |
| Finality and reconciliation | Live commitment level, whether events can disappear or be replayed, rollback signals, and the REST reconciliation boundary | Do not treat provisional events as confirmed; preserve unresolved fork and replay gaps |
| Wallet track record | Raw wallet trade history and separate provider PnL summaries | Treat provider PnL as a comparison field, not a ground-truth ledger |

## Public RPC feasibility finding (2026-11-26)

The public Solana mainnet HTTP/PubSub endpoints require no project API key, but Solana documents them as shared, rate-limited, and not for production. The logged limits are volatile; current pages list 100 requests per 10 seconds per IP, 40 per single RPC, 40 concurrent connections per IP, and 100 MB per 30 seconds. Verify actual reachability and service terms from the intended environment before repeated capture.

For low-latency study, `processed` logs are provisional and may be skipped; full transaction retrieval through `getTransaction` requires confirmed/finalized commitment, with `maxSupportedTransactionVersion: 1` set for v1 support. Therefore event receipt and decoded transaction availability can occur at different times. Preserve both local receipt time and chain slot, and retain a provisional/finality state.

A reconnect must backfill each watched address using `getSignaturesForAddress` pages of at most 1,000 results, then fetch and decode transactions. The public documentation does not promise archival retention or complete recovery. The all-venue universe also needs a separately versioned program/decoder registry; one `mentions` subscription does not imply cross-venue completeness. This supports only a bounded alert-only experiment proposal; it does not change D-004.

## Gate 3 — produce the comparison result

Return a source-by-source evidence matrix with:

- the fields present, absent, or inconsistent for each event family;
- observed overlap and mismatches against the independent reference, if available;
- duplicate, ordering, attribution, amount, fee, pagination, and recovery findings;
- empirical receive-time measurements, clearly distinguished from source first-seen time;
- documentation or account limits that constrain the sample; and
- unresolved legal, territorial, and reuse conditions.

Do not introduce numeric pass thresholds, weights, or a provider ranking without an explicit project decision. A provider recommendation must explain its missing evidence and must not claim universal venue coverage from a sample.

## Decision gate

After the comparison, document the evidence and recommendation in the decision brief. A provider decision must be explicitly approved and recorded before adding network code. Until then, the result remains research-only and D-004 remains unchanged.