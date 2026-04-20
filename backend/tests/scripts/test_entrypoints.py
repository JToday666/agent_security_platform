from __future__ import annotations

import os
import runpy
from pathlib import Path
from unittest.mock import patch

import pytest

from app.shared.config import settings


pytestmark = pytest.mark.scripts


def test_run_py_entrypoint_invokes_uvicorn(backend_root: Path) -> None:
    original_cwd = Path.cwd()
    try:
        with patch("uvicorn.run") as run_mock:
            runpy.run_path(str(backend_root / "run.py"), run_name="__main__")
    finally:
        os.chdir(original_cwd)

    run_mock.assert_called_once_with(
        "app.main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=True,
    )


def test_worker_py_entrypoint_invokes_worker_main(backend_root: Path) -> None:
    with patch("app.worker.main.main") as main_mock:
        runpy.run_path(str(backend_root / "worker.py"), run_name="__main__")

    main_mock.assert_called_once_with()

