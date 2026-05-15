from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from app.worker import main as worker_main

pytestmark = pytest.mark.worker


def test_build_worker_id_is_unique_per_call() -> None:
    first = worker_main.build_worker_id()
    second = worker_main.build_worker_id()

    assert first.startswith("worker-")
    assert second.startswith("worker-")
    assert first != second


def test_main_starts_runner_with_generated_worker_id() -> None:
    with patch.object(
        worker_main, "build_worker_id", return_value="worker-test"
    ) as build_mock, patch.object(
        worker_main,
        "run_worker_loop",
        new=Mock(return_value="runner-coro"),
    ) as loop_mock, patch.object(
        worker_main.asyncio, "run"
    ) as asyncio_run_mock:
        worker_main.main()

    build_mock.assert_called_once_with()
    loop_mock.assert_called_once_with("worker-test")
    asyncio_run_mock.assert_called_once_with("runner-coro")
