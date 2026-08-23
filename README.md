# MoyBot

Event-driven, delta-first crypto-trading intelligence pipeline.

> We don't want to be the fastest bot.
> We want to be the fastest bot that still has enough information to make the right decision.

`PROJECT_SPEC.md` is the primary specification. `docs/DECISIONS.md` records the approved
decisions, and `docs/PHASE1_SCOPE.md` and `docs/PHASE2_SCOPE.md` state exactly what this scaffold
does and does not do.

**This is still an offline scaffold.** It ships no thresholds, weights, or detection logic, makes
no network calls, and cannot trade: the only action is a structured-log alert. With the shipped
configuration a replay produces `not_configured` decisions and raises no alert — by design.

Phase 2 made the final pre-trade validation of `PROJECT_SPEC.md` §5 real: before acting, the
pipeline re-reads the token's state through a fresh-state port and compares it with the state the
decision was made on. Offline, that read is answered by the replay fixture.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv python install 3.12
uv sync --all-groups
uv run pre-commit install
```

## Run

Replay a fixture through the whole pipeline:

```bash
uv run moybot --fixture tests/fixtures/smart_wallet_buy.json --data-dir ./.moybot-data
```

Optionally pass a configuration file (`--config config/pipeline.example.toml`). Snapshots and
provenance are written as newline-delimited JSON under the data directory.

## Checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

Regenerate the provenance golden file after a deliberate schema change:

```bash
uv run python -m tests.golden.regenerate
```

## Layout

```text
src/moybot/core/      pipeline, domain model, state, snapshots, delta, events, filtering,
                      analysis, scoring, strategies, validation, action
src/moybot/adapters/  replay/fixture ingestion and fresh-state reads (the only adapter)
src/moybot/app/       configuration, composition root, CLI
tests/                unit, property, and integration tests plus replay fixtures
```
