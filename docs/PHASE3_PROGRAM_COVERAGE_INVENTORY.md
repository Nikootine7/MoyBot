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
| Meteora DLMM | `LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo` | Bin-based pools, swaps, and liquidity positions | [Meteora DLMM program/event reference](https://github.com/MeteoraAg/docs/blob/main/developer-guides/dlmm/program/events.mdx) |
| Orca Whirlpools | `whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc` | Concentrated-liquidity pools, swaps, and liquidity positions | [Orca Whirlpools repository](https://github.com/orca-so/whirlpools) |
| Liquid bonding curve | `LiquidsqH2a9gsPRf1M2QFhFqfLXWYTDZGzbsNQCDux` | Token launch, curve trades, and migration | [Liquid protocol overview](https://docs.liquid.af/protocol/overview); [official IDL/program IDs](https://docs.liquid.af/sdk/idl) |
| Liquid Swap | `SwapMXcpJdXgnFG9BZak2fBZUiNeR2qYxzexF2ZxdW8` | Graduated CPMM pools, swaps, deposits, and withdrawals | [Liquid protocol overview](https://docs.liquid.af/protocol/overview); [official IDL/program IDs](https://docs.liquid.af/sdk/idl) |
| MetaDAO Launchpad v0.7 | `moontUzsdepotRGe5xsfip7vLPTJnVuafqdUWexVnPM` | Launchpad program listed as current v0.7 by MetaDAO | [MetaDAO program addresses](https://metadao.com/docs/protocol-analytics) |
| MetaDAO Futarchy v0.6 | `FUTARELBfJfQ8RDGhg1wdhddq1odMAJUePHFuBYfUxKq` | Futarchy program address listed by MetaDAO for v0.6; verify active deployment/version before using | [MetaDAO program addresses](https://metadao.com/docs/protocol-analytics) |

These rows are a useful first registry, not a complete universe. Liquid and MetaDAO rows are sourced from their respective protocol docs; preserve the published version labels, and verify the current deployment before relying on them. The Liquid Swap address is the one documented by Liquid.af; its exact equivalence to any third-party provider's venue label has not been independently checked. Other protocols, versions, and newly deployed programs may be absent.

## Bounded address sanity check

On 2026-11-26, the connected read-only Solana Tracker account-info tool resolved all 16 addresses in the table with `exists=true`, `executable=true`, and owner `BPFLoaderUpgradeab1e11111111111111111111111`. Three calls initially returned a wrapper-level `Forbidden`; individual retries succeeded. The tool has no cluster selector and did not return a deployed-code hash, so this is only an address/executable sanity check. It does not verify mainnet deployment/version, current activity, IDL compatibility, or decoder/event coverage.

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

## Candidate raw transaction fixture (2026-11-27)

[research/fixtures/transactions/meteora-damm-v2-swap-v0-candidate.json](../research/fixtures/transactions/meteora-damm-v2-swap-v0-candidate.json) is an exact copy of a user-provided getTransaction-shaped response. The payload does not identify the RPC endpoint, cluster, or commitment, and no independent chain lookup was performed. Treat it as an **unverified candidate**, not confirmed mainnet-beta coverage. Meteora documents the same DAMM v2 program ID on mainnet-beta and devnet, so matching the program ID cannot establish the cluster ([program IDs](https://github.com/MeteoraAg/damm-v2/blob/8ea1d74d92ea843f0348d6875654ee7fbe765dc5/README.md)).

The response reports slot 474558089, block time 1795784195, transaction version 0, and success. Top-level instruction index 3 invokes the DAMM v2 Swap; its inner event-CPI decodes as EvtSwap2 for pool AvJS1QnhNjNNqaqzh2Eady9XS4QbARrpuSXVW48mz1mf, direction token A → token B, exact-in. The event reports 2,504,224,549 raw input units of token A (6 decimals; Token-2022) and 122 raw output units of wrapped SOL (9 decimals). Schema references are pinned to [Meteora's event.rs at commit 8ea1d74](https://github.com/MeteoraAg/damm-v2/blob/8ea1d74d92ea843f0348d6875654ee7fbe765dc5/programs/cp-amm/src/event.rs) and the [SDK IDL at commit eab5e8a](https://github.com/MeteoraAg/damm-v2-sdk/blob/eab5e8aaa951418db43abbac471d9762b2005f11/src/idl/cp_amm.json); see also the [DAMM v2 event reference](https://github.com/MeteoraAg/docs/blob/main/developer-guides/damm-v2/program/events.mdx).

This is a useful accounting edge case: the transaction creates and closes a temporary WSOL account, charges a 10,000-lamport network fee, includes a separate 5,000-lamport System Program transfer, and returns 122 lamports of swap output. The fee payer's net SOL delta is therefore -14,878 lamports. A decoder that infers the swap only from net SOL balance change would miss or misclassify this trade. Do not assign a purpose to the separate transfer without more provenance.

One transaction does not establish event coverage, venue completeness, a wallet label, or Smart Wallet status. Preserve the original raw response and its unknown provenance until the RPC source, cluster, and commitment can be confirmed.

## Gaps and next qualification work

1. Confirm the remaining D-013 protocol families and versions against authoritative references; this bounded list does not prove complete venue coverage.
2. Resolve launchpad-brand-to-config mappings (including any aliases surfaced by the source), separately from the shared program registry.
3. Keep the Meteora response as an unverified candidate until its RPC source, cluster, and commitment are confirmed; then collect independently confirmed signatures and per-family instruction fixtures, and measure missed or ambiguous lifecycle events.
4. Only after source access and D-004 are explicitly resolved, qualify a bounded ingestion path and backfill/reconnect behavior. Public RPC's one-address-per-`logsSubscribe` filter makes the registry size and per-address request/message budget part of that experiment.

No runtime code, API credential, provider selection, event rule, or test was added. The sample is a single unverified research fixture, not a coverage claim. D-004 remains in force; D-013 remains the broad offline research scope.
