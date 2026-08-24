# Phase 2 scope

Phase 2 makes the FINAL PRE-TRADE VALIDATION gate of `PROJECT_SPEC.md` §5 real and auditable,
offline, without deciding a single OPEN QUESTION.

Read this together with `docs/DECISIONS.md` (D-009..D-012) and `docs/PHASE1_SCOPE.md`, which
remains an accurate description of everything Phase 2 does not change.

## Why

Phase 1 wired §5 into the pipeline but the validator re-captured a snapshot from the same
in-process cache, in the same synchronous step that had just produced the decision snapshot. The
two states were therefore identical by construction, so the check could cancel on staleness or on
an unknown field but never on actual deterioration — the reason the stage exists. Phase 2 replaces
that self-comparison with a genuine fresh-state read.

## In scope

| Area | Phase 2 state |
| --- | --- |
| Fresh-state read (§5) | `StateRefresher` port in `core/ingestion/refresh_port.py`; a read returns state or reports itself unavailable |
| Replay refresher | `adapters/replay/refresher.py` answers from state the fixture declares alongside the observation being replayed |
| Fixture schema | v2 adds an optional `validation_state` block per update (D-010, still EXPERIMENTAL) |
| Validation (§5) | Refresh is mandatory; the decision snapshot is compared against the refreshed state; unavailable or stale refresh cancels (D-011) |
| Time in replays | Staleness is measured against fixture-derived observation time via an injected clock (D-009) |
| Provenance (§4) | Validation records carry the checked snapshot's slot and capture time, the measured age and slot lag, every compared volatile value, and the named limit that cancelled |
| Provenance (§4) | `continuous_data` now records its successful outcome, not only `no_state` |
| Typing | Reported metric fields are a closed `MetricValue` union; the cache merges them field by field, with no `type: ignore` and no reflection |
| Configuration | `.env.example` deleted; no environment-variable overrides exist (D-012) |

No new limit, threshold, weight, or detection rule is introduced. The seven deterioration limits
and two staleness limits are the ones Phase 1 already defined, and they remain unset in the
shipped configuration, so a default replay still cancels everything and raises no alert.

## Out of scope

Unchanged from Phase 1, and explicitly: real providers, Solana RPC or any network call, wallet
keys, signing, transaction construction, execution, Bot C, the Smart Wallet definition, scoring
weights, score thresholds, hard-rejection rules, staleness and deterioration *values*, latency
targets, retention or pruning, alert destinations beyond stdout, and concurrency or throughput
work.

## How a fresh read differs from an observation

A refreshed read is *state*, not an observation from the stream. It is merged onto what continuous
state already knows, so an unreported field keeps its last observed value, but the result is only
ever a snapshot: continuous state itself is not written to. Otherwise the read would become the
baseline for the next event's decision snapshot and delta, and the check would again be comparing
a state against itself. A read never becomes an event, a delta, or a scored input; events still
come only from the source (`AGENTS.md`).

Smart-wallet fields in a refreshed read are the fields the source declares, exactly as in Phase 1.
Phase 2 compares them; it does not define what a Smart Wallet is.

## Fixture format v2 (EXPERIMENTAL, not a provider contract)

```json
{
  "schema_version": 2,
  "name": "deterioration_before_action",
  "updates": [
    {
      "mint": "<base58 mint>",
      "slot": 101,
      "observed_at_ms": 1750000000400,
      "price": "0.00000450",
      "events": [{ "kind": "smart_wallet_buy", "payload": { "wallet": "<base58>" } }],
      "validation_state": {
        "slot": 102,
        "observed_at_ms": 1750000000600,
        "liquidity": "20000.00"
      }
    }
  ]
}
```

Rules, in addition to the Phase 1 rules:

* `validation_state` is the answer a fresh read gets while that observation is being replayed. It
  is not a further observation: it raises no event and produces no delta.
* An update without `validation_state` makes the read unavailable, which cancels validation.
* Schema v1 fixtures no longer load.

## Storage layout

Unchanged, except that a replay now derives both partition dates from the fixture rather than
taking the provenance date from the wall clock (D-009).

## Phase 3 blockers (unchanged by Phase 2)

The Smart Wallet definition (§9) is still the first blocker, then the provider choice, scoring
weights and thresholds, the staleness limits, and the latency target. Phase 2 additionally leaves
open how a live source answers a fresh read, where "current slot" comes from once one exists, and
whether refresh should be per-strategy.
