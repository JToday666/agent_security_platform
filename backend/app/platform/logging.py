"""Logging setup helpers for API, scheduler and worker processes."""

from __future__ import annotations

import logging

from app.platform.config import settings

_CONFIGURED = False


def configure_logging() -> None:
    """Configure stdlib logging once per process."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = (settings.LOG_LEVEL or "INFO").strip().upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    _CONFIGURED = True
