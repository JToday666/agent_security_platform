from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path


def test_no_legacy_backend_import_paths_remain(backend_root: Path) -> None:
    target_files = [
        *backend_root.joinpath("app").rglob("*.py"),
        backend_root / "run.py",
        backend_root / "alembic" / "env.py",
    ]
    forbidden_patterns = [
        "app.api.v1.endpoints",
        "app.services",
        "app.crud",
        "app.core",
        "app.db",
        "app.api.response",
        "app.api.deps",
        "app.schemas",
    ]

    violations: list[str] = []
    for path in target_files:
        source = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern in source:
                violations.append(f"{path.relative_to(backend_root)} -> {pattern}")

    assert violations == []


def test_legacy_compatibility_files_are_removed(backend_root: Path) -> None:
    legacy_paths = [
        "app/api/v1/endpoints/auth.py",
        "app/api/v1/endpoints/user.py",
        "app/api/v1/endpoints/datasets.py",
        "app/api/v1/endpoints/agents.py",
        "app/api/v1/endpoints/evaluations.py",
        "app/services/__init__.py",
        "app/services/datasets.py",
        "app/services/evaluations.py",
        "app/services/runtime_rules.py",
        "app/services/secret_store.py",
        "app/services/simulator.py",
        "app/services/submissions.py",
        "app/crud/__init__.py",
        "app/crud/user.py",
        "app/core/config.py",
        "app/core/security.py",
        "app/db/base.py",
        "app/db/session.py",
        "app/schemas/__init__.py",
        "app/schemas/agents.py",
        "app/schemas/auth.py",
        "app/schemas/base.py",
        "app/schemas/datasets.py",
        "app/schemas/evaluations.py",
        "app/schemas/user.py",
        "app/api/deps.py",
        "app/api/response.py",
    ]

    remaining = [path for path in legacy_paths if (backend_root / path).exists()]
    assert remaining == []


def test_auth_dependency_and_shared_boundaries() -> None:
    assert importlib.util.find_spec("app.modules.auth.dependencies") is not None

    auth_module = importlib.import_module("app.shared.auth")
    assert hasattr(auth_module, "get_db")
    assert not hasattr(auth_module, "get_current_user")

    runtime_rules_module = importlib.import_module("app.shared.runtime_rules")
    assert hasattr(runtime_rules_module, "difficulty_bucket_bounds")
    assert hasattr(runtime_rules_module, "is_valid_request_id")
    assert not hasattr(runtime_rules_module, "build_controls")
    assert not hasattr(runtime_rules_module, "apply_pause_timeout")
    assert not hasattr(runtime_rules_module, "TERMINAL_STATUSES")
    assert importlib.util.find_spec("app.shared.run_lifecycle") is None


def test_worker_refactor_boundaries() -> None:
    assert importlib.util.find_spec("app.worker.processing") is not None
    assert importlib.util.find_spec("app.worker.execution") is not None
