"""Worker 进程入口。"""

from __future__ import annotations

import asyncio
import os
import socket
import uuid

from app.worker.sample_worker import run_sample_worker_loop


def build_worker_id() -> str:
    """生成当前 worker 的唯一标识。"""
    return f"worker-{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:8]}"


def main() -> None:
    """启动 worker 主循环。"""
    asyncio.run(run_sample_worker_loop(build_worker_id()))


if __name__ == "__main__":
    main()
