from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from tests.helpers.scripts import load_module_from_path


pytestmark = pytest.mark.scripts


def load_http_smoke_module(backend_root: Path):
    return load_module_from_path(
        f"http_smoke_check_{uuid4().hex}",
        backend_root / "scripts" / "http_smoke_check.py",
    )


def test_http_smoke_script_exists_and_supports_help(backend_root: Path) -> None:
    script_path = backend_root / "scripts" / "http_smoke_check.py"
    assert script_path.exists()

    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Run live HTTP smoke checks" in result.stdout


def test_parse_args_supports_base_url_timeout_and_keep_data(backend_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_http_smoke_module(backend_root)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "http_smoke_check.py",
            "--base-url",
            "http://127.0.0.1:9000",
            "--timeout",
            "12.5",
            "--keep-data",
        ],
    )

    args = module.parse_args()

    assert args.base_url == "http://127.0.0.1:9000"
    assert args.timeout == 12.5
    assert args.keep_data is True


def test_check_envelope_rejects_nonstandard_response_shape(backend_root: Path) -> None:
    module = load_http_smoke_module(backend_root)

    class DummyResponse:
        def __init__(self) -> None:
            self.status_code = 200
            self.request = SimpleNamespace(
                method="GET",
                url=SimpleNamespace(path="/api/v1/demo"),
            )
            self.text = '{"message":"missing fields"}'

        def json(self):
            return {"message": "missing fields"}

    with pytest.raises(AssertionError):
        module.check_envelope(DummyResponse(), status_code=200)

