from __future__ import annotations

import asyncio
import os
import socket
import uuid

from app.worker.runner import run_worker_loop


def build_worker_id() -> str:
    return f"worker-{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:8]}"


def main() -> None:
    asyncio.run(run_worker_loop(build_worker_id()))


if __name__ == "__main__":
    main()
