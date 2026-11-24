# Phase 3 Proposal: Smart Wallet Discovery

**Status: PROPOSED.** This document is a research and implementation plan, not an approved wallet definition, scoring model, provider choice, or trading rule. It introduces no thresholds, weights, or risk limits.

## Goal

Resolve the first Phase 3 blocker in `PROJECT_SPEC.md` §9: define what evidence would make wallet activity useful to Bot A and Bot B, then determine whether the current data model can measure that evidence.

The project remains Solana-focused (D-001). Bot A and Bot B retain separate purposes and configuration (D-006). A wallet event is evidence entering the pipeline, not an instruction to copy its trade or execute an order.

## What the repository currently represents

- `WalletActivity` records wallet, mint, direction, slot, timestamp, and one optional `amount`. The amount's denomination is unspecified.
- `WalletHistory` groups observed activities and first/last slots. The cache can store it, but the replay fixture does not represent wallet activity or feed wallet histories into the pipeline.
- `TokenMetrics.smart_wallet_addresses` and `smart_wallet_transaction_count` are source-reported values. MoyBot does not currently derive a wallet classification.
- The current activity model does not record transaction signature, quote-side input/output, fees, or execution price. It therefore cannot independently reconstruct realized net PnL or a follower's executable return.

These are observations about the current scaffold, not requirements for a particular provider or schema.

## Separate two questions

“Is this a skilled wallet?” and “Is this wallet's activity a useful MoyBot signal?” are related but different.

1. **Wallet track record:** How has the wallet performed on prior token positions, using only information available before the current signal?
2. **Signal value:** If MoyBot observes this wallet's trade at a particular slot, what outcome could MoyBot plausibly achieve after its own data and decision delay, under the token's liquidity and execution conditions?

A wallet can have a strong historical record while a particular buy is already too late or too illiquid to follow. Conversely, an early trade may be useful to Bot B even when the wallet lacks a long history. The proposal is to measure these separately and let each strategy consume them according to its own approved policy. No wallet should receive an eternal, context-free “smart” label by default.

## Proposed evaluation protocol

### 1. Define the observation point

Use a wallet–mint–event-time record: wallet (W) traded mint (M) at slot (S), with the information available to MoyBot at that point.

All features for a prediction must be computable from data available at or before (S). Wallet labels or token outcomes from later slots must never leak into that event's features.

### 2. Measure both wallet performance and actionable signal performance

Where full trade accounting is available, evaluate the wallet's realized position outcome after trading costs. Separately simulate a MoyBot entry only after the wallet event could have been observed and processed. Include the resulting price impact, slippage, fees, failed or delayed execution, and liquidity constraints where the source data supports them.

Report distributions and downside as well as averages: sample count, median and spread of returns, losing-tail outcomes, drawdown, and consistency across time and token conditions. These are candidate diagnostics, not approved score fields or cutoffs.

### 3. Test out of sample

Use chronological evaluation. Build each event's features only from earlier observations, include failed and abandoned tokens in the evaluation universe, and test across later time periods. Report results separately by token age, liquidity, and other measured conditions so a market regime or token-selection effect is not mistaken for wallet skill.

Test timing sensitivity rather than assuming the wallet's own fill is reproducible. Any delay values or execution assumptions must be disclosed and approved before they become production rules.

### 4. Keep the two strategy goals distinct

- **Bot A:** evaluate whether repeatable wallet evidence adds confidence and reduces bad candidates, alongside token-level risk checks.
- **Bot B:** evaluate whether the earliest useful wallet activity predicts asymmetric upside before broad confirmation arrives. Do not make it wait for a large count of wallets merely because that works for Bot A.

This section restates the existing strategy intent; it does not set weights, thresholds, or entry rules.

## Relevant research

Luo et al. (2026), [“Resisting Manipulative Bots in Meme Coin Copy Trading”](https://arxiv.org/abs/2601.08641), analyze wallet selection together with token conditions and entry timing. Their historical evaluation uses transaction data for 6,000 pump.fun projects and pump.fun comments; the paper describes a chronological train/validation/test split and labels positions by the sign of realized wallet profit. It also explains why a profitable wallet does not guarantee a profitable follower: later fills can be worse because of bonding-curve price impact.

**Use for MoyBot:** this supports testing wallet, token, and timing evidence together, and measuring the follower's own possible fill rather than copying the wallet's result.

**Limit:** the study is specific to pump.fun copy trading and its historical data and execution model. Its results do not establish MoyBot's wallet definition, provider, profitability, or live performance, and are not adopted as project targets.

## Proposed order of work

1. Decide whether “Smart Wallet” is a historical wallet-quality label, an actionable event signal, or both. **Proposal:** preserve separate evidence for both questions.
2. Inventory any available wallet addresses, transaction exports, and data coverage.
3. Define a provider-neutral minimum trade record from that inventory, including amount units and the fields needed to estimate net outcomes.
4. Compare candidate Solana data sources against that record and the required history, slot ordering, latency, and cost.
5. Only then implement wallet-history ingestion and an evaluation module. Keep unknown or insufficient history distinct from a poor wallet score.

## Questions for project owner

- Is there an existing candidate-wallet list or historical transaction export we can use for the data inventory?
- Should the initial universe cover all Solana token venues, or begin with a specific launch or pool segment? This affects data coverage and must not be guessed.
