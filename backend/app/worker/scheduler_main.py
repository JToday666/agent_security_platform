"""Scheduler process entrypoint."""

from __future__ import annotations

import asyncio

from app.platform.logging import configure_logging
from app.worker.sample_scheduler import run_scheduler_loop


def main() -> None:
    """Start the sample scheduler and finalizer loop."""
    configure_logging()
    asyncio.run(run_scheduler_loop())


if __name__ == "__main__":
    main()
