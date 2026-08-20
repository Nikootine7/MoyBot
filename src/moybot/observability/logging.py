"""Structured logging configuration.

Logs go to stdout as JSON so that stage outcomes and timings are machine-readable. Timings are
reported, never enforced: the latency target is an OPEN QUESTION (PROJECT_SPEC.md §9).
"""

from __future__ import annotations

import logging
import sys

import structlog

__all__ = ["configure_logging"]


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog to emit JSON lines on stdout."""
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level.upper())
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(sort_keys=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[level.upper()]
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
