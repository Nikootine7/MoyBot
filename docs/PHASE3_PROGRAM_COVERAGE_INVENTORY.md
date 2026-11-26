# Phase 3 initial program-coverage inventory

**Status: RESEARCH INVENTORY — incomplete.** This is a dated mainnet-beta address and decoder checklist for D-013's offline all-venue research universe. It is not a production allowlist, decoder implementation, or claim of complete Solana coverage.

**Reviewed:** 2026-11-26. Program IDs and protocol interfaces can change; re-check the protocol's current docs/IDL and the deployed program before any implementation.

## Initial protocol program set

| Protocol family / label | Mainnet program ID | Role in the event graph | Primary program reference |
| --- | --- | --- | --- |
| Pump bonding curve | `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` | Launch, pre-graduation curve activity, and migration instruction | [Pump Program docs and IDL](https://github.com/pump-fun/pump-public-docs/blob/main/docs/PUMP_PROGRAM_README.md) |
| PumpSwap | `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA` | Post-migration AMM pools and pool activity | [PumpSwap docs and IDL](https://github.com/pump-fun/pump-public-docs/blob/main/docs/PUMP_SWAP_README.md) |
| Raydium LaunchLab | `LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj` | Launch curve, initialization, and graduation/migration | [Canonical Raydium program addresses](https://github.com/raydium-io/raydium-docs-v1/blob/main/reference/program-addresses.mdx); [LaunchLab lifecycle](https://github.com/raydium-io/raydium-docs-v1/blob/main/products/launchlab/overview.mdx) |
| Raydium AMM v4 | `675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8` | Legacy pool, swap, and liquidity activity | [Canonical Raydium program addresses](https://github.com/raydium-io/raydium-docs-v1/blob/main/reference/program-addresses.mdx) |
| Raydium CPMM | `CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C` | Constant-product pool, swap, and liquidity activity | [Canonical Raydium program addresses](https://github.com/raydium-io/raydium-docs-v1/blob/main/reference/program-addresses.mdx) |
| Raydium CLMM | `CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK` | Concentrated-liquidity pool, swap, and position/liquidity activity | [Canonical Raydium program addresses](https://github.com/raydium-io/raydium-docs-v1/blob/main/reference/program-addresses.mdx) |
| Raydium Stable AMM | `5quBtoiQqxF9Jv6KYKctB59NT3gtJD2Y65kdnB1Uev3h` | Stable-swap pool activity | [Canonical Raydium program addresses](https://github.com/raydium-io/raydium-docs-v1/blob/main/reference/program-addresses.mdx) |
| Meteora Dynamic Bonding Curve (DBC) | `dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN` | Launch curve, curve trades, and graduation/migration | [Meteora DBC developer guide](https://docs.meteora.ag/developer-guides/dbc/) |
| Meteora DAMM v1 | `Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB` | Legacy dynamic-AMM pools and activity | [Meteora DAMM v1 SDK](https://github.com/MeteoraAg/damm-v1-sdk) |
| Meteora DAMM v2 / cp-amm | `cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG` | Constant-product/dynamic-fee pools, including DBC migration destination | [Meteora DAMM v2 developer guide](https://docs.meteora.ag/developer-guides/damm-v2/) |
| Meteora DLMM | `LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo` | Bin-based pools, swaps, and liquidity positions | [Meteora DLMM program/event reference](https://docs.meteora.ag/developer-guides/dlmm/program/events) |
| Orca Whirlpools | `whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc` | Concentrated-liquidity pools, swaps, and liquidity positions | [Orca Whirlpools repository](https://github.com/orca-so/whirlpools) |

These rows are a useful first registry, not a complete universe. Solana Tracker's liquidity guide also names Liquid Swap and Futarchy, but this inventory has not yet confirmed their program IDs and authoritative decoder/IDL sources. Other protocols and newly deployed programs may be absent.

## Venue labels are not always program IDs

A branded launchpad can use a shared underlying program. Jupiter's official [Studio overview](https://developers.jup.ag/docs/studio/index.md) describes token launches on Dynamic Bonding Curve pools; record the Jupiter Studio venue attribution separately from the Meteora DBC program ID. A program match alone cannot prove a launchpad brand. Capture platform/config accounts or source-provided venue labels and leave attribution unknown until the mapping is verified. Likewise, identify a migration from the transaction's actual instructions and destination pool/program; do not infer it from the launchpad name.

## Decoder coverage required before a coverage claim

For each row, pin and retain the protocol's current IDL/schema version (repository commit or content hash), cluster, instruction discriminators, account layouts, and relevant event/log definitions. The decoder qualification must cover:

- launch/initialize, curve buy/sell, pool initialize, swap, liquidity add/remove, and migration/complete instructions where that family supports them;
- both top-level and inner/CPI instructions, including loaded addresses for versioned transactions;
- exact token/quote mints and raw amount units, and separate wallet, owner, fee-payer, pool, venue, and program identities;
- chain slot, transaction signature, transaction/instruction indices, success/error state, and nullable provider first-seen / receiver timestamps;
- SPL Token and Token-2022 account/balance handling where present; and
- transaction fixtures for every supported instruction variant, including current and legacy variants where applicable.

A program-address match by itself is not a decoded trade or a pool event. Anchor instruction discriminators can collide across protocols; always match the program ID and instruction layout together. Preserve raw instruction provenance and unknown fields before normalization.

## Gaps and next qualification work

1. Add authoritative IDL/program references for Liquid Swap, Futarchy, and other discovered families before claiming the D-013 universe is covered.
2. Resolve launchpad-brand-to-config mappings (including any aliases surfaced by the source), separately from the shared program registry.
3. Build a per-family instruction matrix and collect confirmed transaction signatures for replay; measure which lifecycle events are missed or ambiguous.
4. Only after source access and D-004 are explicitly resolved, qualify a bounded ingestion path and backfill/reconnect behavior. Public RPC's one-address-per-`logsSubscribe` filter makes the registry size and per-address request/message budget part of that experiment.

No runtime code, API credential, provider selection, event rule, or test was added or authorized by this inventory. D-004 remains in force; D-013 remains the broad offline research scope.
