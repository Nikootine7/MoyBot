"""CLI entrypoint.

Replays a fixture through the full pipeline and reports what each stage did. Alert-only and
offline (docs/DECISIONS.md D-003, D-004): this command cannot place an order.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import structlog

from moybot.adapters.replay.session import open_replay
from moybot.app.composition import build_pipeline
from moybot.app.config import load_config
from moybot.app.localization import Language, replay_completed_message
from moybot.core.pipeline.runner import UpdateResult
from moybot.observability.logging import configure_logging

__all__ = ["main"]


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="moybot",
        description=(
            "Replay a fixture through the MOYBOT pipeline (offline, alert-only). / "
            "اجرای آفلاین و فقط هشدارِ فایل بازپخش در خط لولهٔ موی‌بات."
        ),
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        required=True,
        help="path to a replay fixture / مسیر فایل بازپخش",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="path to a TOML config file / مسیر فایل تنظیمات TOML",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help=(
            "override the directory for snapshots and provenance / "
            "مسیر ذخیره‌سازی snapshot و provenance"
        ),
    )
    parser.add_argument(
        "--language",
        choices=("en", "fa"),
        default=None,
        help="override the display language (en or fa) / تغییر زبان نمایش (en یا fa)",
    )
    return parser.parse_args(argv)


async def _run(
    fixture: Path,
    config_path: Path | None,
    data_dir: Path | None,
    language: Language | None = None,
) -> int:
    config = load_config(config_path)
    selected_language = language if language is not None else config.display.language
    configure_logging(config.logging.level)
    logger = structlog.get_logger("moybot.cli")

    # The replay supplies its own time, so staleness is judged against when the data was
    # observed rather than when the replay runs (docs/DECISIONS.md D-009).
    session = open_replay(fixture)
    pipeline = build_pipeline(
        config,
        clock=session.clock,
        refresher=session.refresher,
        data_dir=data_dir,
        language=selected_language,
    )
    results: tuple[UpdateResult, ...] = await pipeline.runner.run_source(session.source)

    logger.info(
        "replay_completed",
        message=replay_completed_message(selected_language),
        source=session.source.name,
        updates=len(results),
        events=sum(len(result.events) for result in results),
        decisions=sum(len(result.decisions) for result in results),
        alerts=sum(len(result.alerts) for result in results),
        provenance_records=sum(len(result.records) for result in results),
        strategies=[strategy.name for strategy in pipeline.strategies],
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    args = _parse_args(argv)
    return asyncio.run(_run(args.fixture, args.config, args.data_dir, args.language))


if __name__ == "__main__":
    raise SystemExit(main())
