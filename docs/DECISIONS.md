# MOYBOT — Decision Log

This file records decisions that have been **explicitly approved**. It exists to satisfy
`PROJECT_SPEC.md` §11 (Source Discipline): a genuinely new final decision is recorded as
`DECISION — [topic]` together with the reasoning behind it.

Rules for this file:

- Only explicitly approved decisions are recorded here.
- A decision recorded here does **not** retroactively make anything in `PROJECT_SPEC.md` final.
  Items listed in `PROJECT_SPEC.md` §9 ("WHAT IS NOT FINAL") remain not final except for the
  precise, scoped statement of the decision below.
- Illustrative numbers, examples, proposals and recommendations are never recorded here.
- `PROJECT_SPEC.md` is never modified to reflect this file.

Status vocabulary (per `PROJECT_SPEC.md` §10.11): FINAL / DECIDED, PROPOSED, EXPERIMENTAL,
OPEN QUESTION, REJECTED.

---

## Phase 1 decisions

All decisions below were approved by the project owner on 2026-08-20. They are **new**
decisions made at that time; none of them was previously final in `PROJECT_SPEC.md`.

Unless stated otherwise, D-001 through D-005 are **Phase 1 scoping decisions**: they decide
what Phase 1 builds, not the permanent architecture of MOYBOT.

### DECISION — D-001 Target chain

**Status:** FINAL / DECIDED (Phase 1 scope)
**Approved:** 2026-08-20 by project owner

Phase 1 models Solana.

Reasoning: `PROJECT_SPEC.md` §9 leaves the chain undecided, and the chain determines the shape
of every domain type (address format, holder semantics, LP/pool semantics, ordering semantics).
A single target chain is required before domain types can be written down honestly. Solana was
chosen by the project owner.

Consequence: domain vocabulary is Solana-shaped — token identity is a mint address, holders are
token-account owners, LP state refers to pool/LP-token state, "dev" refers to mint/update
authority or deployer, and wallets are base58 public keys. Snapshots carry both a wall-clock
millisecond timestamp and a slot, because slot is the only sound ordering key on Solana.

### DECISION — D-002 Language and runtime

**Status:** FINAL / DECIDED
**Approved:** 2026-08-20 by project owner

MOYBOT is implemented in Python.

Reasoning: `PROJECT_SPEC.md` §9 explicitly leaves the technology stack open. Python was chosen
by the project owner. Implementation details of the toolchain (Python 3.12, `uv`, `ruff`,
`mypy --strict`, `pytest`, `structlog`, `asyncio`, `src/` layout, package name `moybot`) were
approved as reversible engineering defaults and may change without a new decision.

### DECISION — D-003 Phase 1 ACTION scope

**Status:** FINAL / DECIDED (Phase 1 scope)
**Approved:** 2026-08-20 by project owner

Phase 1 is alert-only. There is no live execution, no wallet keys, no signing, and no auto-buy.

Reasoning: `PROJECT_SPEC.md` §5 requires a final pre-trade validation gate and §1 anticipates
future automation, but §9 leaves execution infrastructure and auto-buy implementation undecided.
Building an execution path before those decisions exist would mean inventing requirements.

Consequence: the terminal pipeline stage emits a structured alert. No key material, RPC send
path, or transaction construction exists in the repository.

### DECISION — D-004 Phase 1 data source

**Status:** FINAL / DECIDED (Phase 1 scope)
**Approved:** 2026-08-20 by project owner

Phase 1 uses a replay/fixture data-source adapter. No real external provider is chosen or
integrated.

Reasoning: `PROJECT_SPEC.md` §3 and §9 forbid assuming a provider. A replay adapter lets the
full pipeline run end to end, deterministically and offline, without making a provider decision
by accident.

Consequence: no network calls in Phase 1. The fixture format is a Phase 1 artifact, is marked
EXPERIMENTAL, and is explicitly not a provider contract.

### DECISION — D-005 Phase 1 persistence

**Status:** FINAL / DECIDED (Phase 1 scope)
**Approved:** 2026-08-20 by project owner

Phase 1 stores snapshots and provenance records in local file-backed storage
(newline-delimited JSON). No external database is introduced.

Reasoning: `PROJECT_SPEC.md` §4 requires that every meaningful decision be reconstructible from
its snapshot and features. That requirement is about auditability, not about a database. File
storage satisfies it while leaving the storage-technology question open.

Consequence: retention and pruning are not implemented in Phase 1 (see OPEN QUESTIONS below).

### DECISION — D-006 Bot A and Bot B in Phase 1

**Status:** FINAL / DECIDED
**Approved:** 2026-08-20 by project owner

Bot A and Bot B are scaffolded as separate strategies. No thresholds, weights, or domain
constants are invented or hard-coded.

Reasoning: `PROJECT_SPEC.md` §6, §7 and §10.7 require the two bots to remain logically distinct
(Bot B is explicitly not Bot A with a lower threshold), while §9 leaves all thresholds and
weights undecided.

Consequence: each strategy has its own configuration section. Scoring weights and decision
thresholds must be supplied by configuration; their absence is a hard error rather than a
default value.

### DECISION — D-007 Repository layout

**Status:** FINAL / DECIDED
**Approved:** 2026-08-20 by project owner

Phase 1 uses the proposed layout: a `src/moybot` package split into `core` (domain model and
pipeline stages), `adapters` (data sources), `app` (composition root and CLI) and
`observability`, with `core` subpackages named after the canonical pipeline stages of
`PROJECT_SPEC.md` §2.

Reasoning: naming modules after the canonical pipeline preserves the specification's
terminology and keeps the mapping from spec to code auditable.

### DECISION — D-008 Repository visibility and licensing

**Status:** FINAL / DECIDED
**Approved:** 2026-08-20 by project owner

The repository remains private and no license file is added yet.

---

## OPEN QUESTIONS (not decided)

These remain open and are **not** resolved by anything in this file or in the Phase 1 code.
None of them blocks Phase 1.

- OPEN QUESTION — Exact Smart Wallet definition (`PROJECT_SPEC.md` §9). Phase 1 ships no
  detection logic, so it is not required yet; it is expected to be the first Phase 2 blocker.
- OPEN QUESTION — Exact latency target (§9). Phase 1 instruments per-stage timings but asserts
  nothing about them.
- OPEN QUESTION — Scoring weights, score thresholds, wallet-dominance criteria, cluster
  algorithm, rug-detection criteria, contract-analysis methodology (§9).
- OPEN QUESTION — Real data provider and any Solana RPC read path (§9). Phase 1 makes no
  network calls.
- OPEN QUESTION — Alert destinations beyond stdout structured logs.
- OPEN QUESTION — Snapshot and provenance retention/pruning policy.
- OPEN QUESTION — Whether Bot C (§8) should be anticipated in the domain model. Phase 1 omits
  it entirely, since §8 marks it as future architecture only.
