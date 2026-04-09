from __future__ import annotations

import asyncio
import socket

from app.worker.runner import run_worker_loop


def build_worker_id() -> str:
    return f"worker-{socket.gethostname()}"


def main() -> None:
    asyncio.run(run_worker_loop(build_worker_id()))


if __name__ == "__main__":
    main()
