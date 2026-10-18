"""
Structlog configuration: JSON output in production, pretty console in development.
Includes a PII redaction processor.
"""
from __future__ import annotations

import logging
import sys

import structlog

# Fields to scrub from log records (partial match)
_PII_FIELDS = {"email", "password", "rank", "income", "caste", "phone", "mobile"}


def _redact_pii(
    logger: structlog.types.WrappedLogger,
    method: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Replace PII field values with [REDACTED]."""
    for key in list(event_dict.keys()):
        if any(pii in key.lower() for pii in _PII_FIELDS):
            event_dict[key] = "[REDACTED]"
    return event_dict


def configure_logging(log_level: str = "INFO", json_output: bool = True) -> None:
    """Set up structlog with optional JSON or pretty output."""
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _redact_pii,
        structlog.processors.StackInfoRenderer(),
    ]

    if json_output:
        processors: list[structlog.types.Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
