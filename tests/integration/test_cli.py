"""CLI entrypoint."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from moybot.app.main import main
from tests.support import MINT_A


def test_cli_replays_a_fixture_and_persists_state(fixture_dir: Path, tmp_path: Path) -> None:
    exit_code = main(
        [
            "--fixture",
            str(fixture_dir / "smart_wallet_buy.json"),
            "--data-dir",
            str(tmp_path),
        ]
    )
    assert exit_code == 0
    # A replay takes its time from the fixture, so both snapshots and provenance are partitioned
    # by the observation date rather than by the day the replay ran (docs/DECISIONS.md D-009).
    snapshots = tmp_path / "snapshots" / MINT_A / "2025-06-15.ndjson"
    provenance = tmp_path / "provenance" / "2025-06-15.ndjson"
    assert json.loads(snapshots.read_text(encoding="utf-8").splitlines()[0])["mint"] == MINT_A
    stages = [
        json.loads(line)["stage"] for line in provenance.read_text(encoding="utf-8").splitlines()
    ]
    assert stages[0] == "event_trigger"
    assert "action" not in stages


def test_cli_uses_the_example_config(fixture_dir: Path, tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    exit_code = main(
        [
            "--fixture",
            str(fixture_dir / "no_event.json"),
            "--config",
            str(repo_root / "config" / "pipeline.example.toml"),
            "--data-dir",
            str(tmp_path),
        ]
    )
    assert exit_code == 0
    assert not (tmp_path / "provenance").exists()


def test_cli_requires_a_fixture() -> None:
    with pytest.raises(SystemExit):
        main([])
