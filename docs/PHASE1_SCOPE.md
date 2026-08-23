# Phase 1 scope

Phase 1 makes the pipeline in `PROJECT_SPEC.md` §2 executable end to end as a scaffold, offline
and deterministically, without deciding a single undecided domain question.

Read this together with `docs/DECISIONS.md` (D-001..D-008). This document describes Phase 1 as it
shipped; where Phase 2 changed something (final validation, replay time, the fixture schema), the
current behaviour is in `docs/PHASE2_SCOPE.md`.

## In scope

| Area | Phase 1 state |
| --- | --- |
| Pipeline (§2) | All eight canonical stages wired and instrumented |
| Continuous state (§2.1) | In-memory cache of the specified fields, merged per reported field |
| Event trigger (§2.2) | Only events the source declares; no heuristic detects anything |
| Delta analysis (§2.3) | Mechanical snapshot diff over every cached field, no significance rules |
| Candidate filtering (§2.4) | Filter-chain machinery with an accept-all default |
| Heavy analysis (§3) | All specified categories registered, disabled, and erroring if enabled |
| Scoring (§4) | Weighted scorer that requires configured weights and refuses to run without them |
| Bot A / Bot B (§6, §7) | Two separate strategies with separate configuration, no shipped thresholds |
| Final validation (§5) | Fail-closed re-check against fresh state; no shipped limits |
| Action (§9) | Alert-only structured log sink |
| Provenance (§4) | Append-only NDJSON record per stage, including rejections and cancellations |
| Ingestion | Replay/fixture adapter only |

## Out of scope

Real data providers, Solana RPC or any network call, wallet keys, signing, transaction
construction, execution or auto-buy, Bot C, backtesting, social data, real detection logic
(smart-wallet, cluster, rug, wash-trading, contract analysis), scoring weights, score thresholds,
staleness limits, latency targets, retention policies, and alert destinations beyond stdout.

## What "no invented domain constants" means in practice

* No threshold, weight, or limit has a default anywhere in `src/`. Configuration keys exist; the
  values are absent, and absence means "cancel" or "not configured", never "0" and never "allow".
* Unknown data is `None`, not zero. Validation cancels when a volatile field is unknown.
* With the shipped configuration a replay produces decisions with outcome `not_configured` and
  raises no alert. That is the correct Phase 1 behaviour, not a bug.
* Numbers that appear in tests, fixtures, and `config/pipeline.example.toml` comments are test
  inputs or placeholders. None of them is a proposal.

## Fixture format (EXPERIMENTAL, not a provider contract)

`tests/fixtures/*.json` drive the replay adapter. The schema is a scaffold artefact and will be
replaced when a provider is chosen; it is not a claim about any provider's shape. Phase 2 raised
`schema_version` to `2` and added a validation-time state block (`docs/PHASE2_SCOPE.md`); the v1
shape below no longer loads.

```json
{
  "schema_version": 1,
  "name": "smart_wallet_buy",
  "updates": [
    {
      "mint": "<base58 mint>",
      "slot": 101,
      "observed_at_ms": 1750000000000,
      "price": "0.00000450",
      "events": [{ "kind": "smart_wallet_buy", "payload": { "wallet": "<base58>" } }]
    }
  ]
}
```

Rules:

* Only fields present in an update are applied to the cache. Omitted means "not reported", which
  leaves the cached value untouched.
* Quantities are JSON strings and parsed as exact decimals.
* `events` is the *only* source of events. `kind` is an open label, not an enumeration.

## Storage layout

```text
<data_dir>/snapshots/<mint>/<YYYY-MM-DD>.ndjson   # partitioned by observation date
<data_dir>/provenance/<YYYY-MM-DD>.ndjson         # partitioned by record date
```

Append-only, unbounded: retention and pruning are an OPEN QUESTION.

## Phase 2 blockers (unchanged by Phase 1)

The Smart Wallet definition (§9) is the first blocker: no detector, filter, or scorer can carry
real logic until it exists. Then the provider choice, scoring weights and thresholds, staleness
limits, and the latency target.
