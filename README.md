# MoyBot

Event-driven, delta-first crypto-trading intelligence pipeline.

> We don't want to be the fastest bot.
> We want to be the fastest bot that still has enough information to make the right decision.

`PROJECT_SPEC.md` is the primary specification. `docs/DECISIONS.md` records the approved Phase 1
decisions, and `docs/PHASE1_SCOPE.md` states exactly what this scaffold does and does not do.

**Phase 1 is an offline scaffold.** It ships no thresholds, weights, or detection logic, makes no
network calls, and cannot trade: the only action is a structured-log alert. With the shipped
configuration a replay produces `not_configured` decisions and raises no alert — by design.

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
src/moybot/adapters/  replay/fixture ingestion (the only adapter in Phase 1)
src/moybot/app/       configuration, composition root, CLI
tests/                unit, property, and integration tests plus replay fixtures
```
