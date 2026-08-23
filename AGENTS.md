# Working in this repository

`PROJECT_SPEC.md` is the specification and is not edited as part of implementation work. Approved
decisions live in `docs/DECISIONS.md`; Phase 1 boundaries live in `docs/PHASE1_SCOPE.md`.

## Hard rules

* **Never invent a domain constant.** No threshold, scoring weight, staleness limit, latency
  target, or detection rule may be introduced without a recorded decision. Configuration keys may
  exist with no value; absence must mean "not configured" or "cancel", never "0" and never "allow".
* **Unknown is `None`, never zero.** Anything unknown, stale, or unconfigured must fail closed.
* **Events come only from the source.** Nothing may infer an event from metric movements.
* **No network, no keys, no execution.** No provider client, RPC call, wallet key, signing, or
  order path. The only action is an alert.
* **Bot A and Bot B stay separate**, with separate configuration and separate filter chains.
* Illustrative numbers in `PROJECT_SPEC.md`, tests, fixtures, and example configuration are not
  requirements.
* Record a decision in `docs/DECISIONS.md` before relying on it, and preserve the FINAL /
  PROPOSED / EXPERIMENTAL / OPEN QUESTION / REJECTED distinctions.

## Conventions

* Python 3.12, `uv`, `src/` layout, package `moybot`.
* Ports and adapters: `core/` never imports an adapter.
* Frozen dataclasses for domain types; `Decimal` for every quantity; pydantic only for parsing
  configuration and fixtures.
* Every stage outcome after an event is written to provenance, including rejections.
* Cite the specification section when code encodes a specification requirement.

## Checks

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```
