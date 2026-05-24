from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import pytest


def test_platform_kernel_modules_are_available() -> None:
    platform_config = importlib.import_module("app.platform.config")
    platform_http = importlib.import_module("app.platform.http")
    platform_errors = importlib.import_module("app.platform.errors")
    platform_credentials = importlib.import_module("app.platform.credentials")

    assert platform_config.settings is not None
    assert callable(platform_http.success_payload)
    assert platform_errors.DomainError.__name__ == "DomainError"
    assert platform_credentials.FileCredentialStore.__name__ == "FileCredentialStore"


def test_default_storage_roots_are_server_data_paths(monkeypatch) -> None:
    for name in (
        "ASP_DATA_ROOT",
        "DATASET_ROOT_DIR",
        "DATASET_METADATA_ROOT_DIR",
        "UPLOAD_ROOT_DIR",
        "RUNTIME_ROOT_DIR",
        "TMP_ROOT_DIR",
        "LOG_ROOT_DIR",
    ):
        monkeypatch.delenv(name, raising=False)

    platform_config = importlib.import_module("app.platform.config")
    settings = platform_config.Settings(_env_file=None)

    assert settings.data_root == Path("/data/agent-security-platform")
    assert settings.dataset_root == Path("/data/agent-security-platform/data/datasets")
    assert (
        settings.dataset_metadata_root
        == Path("/data/agent-security-platform/data/dataset-registry")
    )
    assert settings.uploads_root == Path("/data/agent-security-platform/data/uploads")
    assert settings.runtime_root == Path("/data/agent-security-platform/runtime")
    assert settings.tmp_root == Path("/data/agent-security-platform/tmp")
    assert settings.log_root == Path("/data/agent-security-platform/logs")


def test_storage_roots_can_be_derived_from_data_root(monkeypatch) -> None:
    for name in (
        "DATASET_ROOT_DIR",
        "DATASET_METADATA_ROOT_DIR",
        "UPLOAD_ROOT_DIR",
        "RUNTIME_ROOT_DIR",
        "TMP_ROOT_DIR",
        "LOG_ROOT_DIR",
    ):
        monkeypatch.delenv(name, raising=False)

    platform_config = importlib.import_module("app.platform.config")
    settings = platform_config.Settings(ASP_DATA_ROOT="/mnt/asp", _env_file=None)

    assert settings.dataset_root == Path("/mnt/asp/data/datasets")
    assert settings.dataset_metadata_root == Path("/mnt/asp/data/dataset-registry")
    assert settings.uploads_root == Path("/mnt/asp/data/uploads")
    assert settings.runtime_root == Path("/mnt/asp/runtime")
    assert settings.tmp_root == Path("/mnt/asp/tmp")
    assert settings.log_root == Path("/mnt/asp/logs")


def test_storage_root_overrides_take_precedence(monkeypatch) -> None:
    for name in (
        "DATASET_ROOT_DIR",
        "DATASET_METADATA_ROOT_DIR",
        "UPLOAD_ROOT_DIR",
        "RUNTIME_ROOT_DIR",
        "TMP_ROOT_DIR",
        "LOG_ROOT_DIR",
    ):
        monkeypatch.delenv(name, raising=False)

    platform_config = importlib.import_module("app.platform.config")
    settings = platform_config.Settings(
        ASP_DATA_ROOT="/mnt/asp",
        DATASET_ROOT_DIR="/srv/datasets",
        DATASET_METADATA_ROOT_DIR="/srv/registry",
        UPLOAD_ROOT_DIR="/srv/uploads",
        RUNTIME_ROOT_DIR="/srv/runtime",
        TMP_ROOT_DIR="/srv/tmp",
        LOG_ROOT_DIR="/srv/logs",
        _env_file=None,
    )

    assert settings.dataset_root == Path("/srv/datasets")
    assert settings.dataset_metadata_root == Path("/srv/registry")
    assert settings.uploads_root == Path("/srv/uploads")
    assert settings.runtime_root == Path("/srv/runtime")
    assert settings.tmp_root == Path("/srv/tmp")
    assert settings.log_root == Path("/srv/logs")


def test_data_root_must_not_resolve_inside_project(monkeypatch) -> None:
    monkeypatch.delenv("ASP_DATA_ROOT", raising=False)

    platform_config = importlib.import_module("app.platform.config")
    settings = platform_config.Settings(
        ASP_DATA_ROOT=str(platform_config.REPO_ROOT / "var" / "backend"),
        _env_file=None,
    )

    with pytest.raises(ValueError, match="ASP_DATA_ROOT.*project directory"):
        _ = settings.data_root


@pytest.mark.parametrize(
    ("field_name", "property_name", "relative_path"),
    [
        ("DATASET_ROOT_DIR", "dataset_root", "backend/data/datasets"),
        (
            "DATASET_METADATA_ROOT_DIR",
            "dataset_metadata_root",
            "backend/data/dataset-registry",
        ),
        ("UPLOAD_ROOT_DIR", "uploads_root", "backend/uploads"),
        ("RUNTIME_ROOT_DIR", "runtime_root", "backend/runtime"),
        ("TMP_ROOT_DIR", "tmp_root", "backend/tmp"),
        ("LOG_ROOT_DIR", "log_root", "backend/logs"),
    ],
)
def test_generated_storage_root_overrides_must_not_resolve_inside_project(
    monkeypatch, field_name: str, property_name: str, relative_path: str
) -> None:
    monkeypatch.delenv(field_name, raising=False)

    platform_config = importlib.import_module("app.platform.config")
    settings = platform_config.Settings(
        ASP_DATA_ROOT="/mnt/asp",
        **{field_name: str(platform_config.REPO_ROOT / relative_path)},
        _env_file=None,
    )

    with pytest.raises(ValueError, match=f"{field_name}.*project directory"):
        _ = getattr(settings, property_name)


def test_database_url_override_normalizes_async_and_sync_drivers(monkeypatch) -> None:
    monkeypatch.delenv("POSTGRES_HOST", raising=False)
    monkeypatch.delenv("POSTGRES_PORT", raising=False)
    monkeypatch.delenv("POSTGRES_DB", raising=False)
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

    platform_config = importlib.import_module("app.platform.config")
    settings = platform_config.Settings(
        DATABASE_URL="postgresql+psycopg://asp_app:secret@127.0.0.1:5432/asp_db",
        _env_file=None,
    )

    assert settings.DATABASE_URL.drivername == "postgresql+asyncpg"
    assert settings.SYNC_DATABASE_URL.drivername == "postgresql+psycopg"
    assert settings.DATABASE_URL.username == "asp_app"
    assert settings.DATABASE_URL.password == "secret"
    assert settings.DATABASE_URL.host == "127.0.0.1"
    assert settings.DATABASE_URL.database == "asp_db"


def test_application_code_uses_platform_kernel_instead_of_shared_imports(
    backend_root: Path,
) -> None:
    target_files = [
        *backend_root.joinpath("app").rglob("*.py"),
        backend_root / "run.py",
        backend_root / "worker.py",
        backend_root / "alembic" / "env.py",
    ]

    violations: list[str] = []
    for path in target_files:
        relative = path.relative_to(backend_root)
        source = path.read_text(encoding="utf-8")
        if "app.shared" in source:
            violations.append(str(relative))

    assert violations == []


def test_dataset_import_pipeline_has_explicit_database_boundary(
    backend_root: Path,
) -> None:
    assert (
        importlib.util.find_spec("app.modules.datasets.ingestion.database") is not None
    )

    pipeline_source = (
        backend_root / "app" / "modules" / "datasets" / "ingestion" / "pipeline.py"
    ).read_text(encoding="utf-8")
    assert "create_engine" not in pipeline_source
    assert "sessionmaker" not in pipeline_source


def test_worker_execution_uses_explicit_persistence_and_job_boundaries(
    backend_root: Path,
) -> None:
    assert importlib.util.find_spec("app.worker.execution_concurrency") is not None
    assert importlib.util.find_spec("app.worker.execution_jobs") is not None
    assert importlib.util.find_spec("app.worker.execution_persistence") is not None

    execution_source = (backend_root / "app" / "worker" / "execution.py").read_text(
        encoding="utf-8"
    )
    forbidden_snippets = [
        "AsyncSessionLocal",
        "select(",
        "update(",
        "delete(",
        "func.",
    ]

    violations = [
        snippet for snippet in forbidden_snippets if snippet in execution_source
    ]
    assert violations == []


def test_business_services_do_not_read_global_settings_or_sessions(
    backend_root: Path,
) -> None:
    service_files = backend_root.joinpath("app", "modules").glob("*/service.py")

    violations: list[str] = []
    for path in service_files:
        source = path.read_text(encoding="utf-8")
        if (
            "app.platform.config import settings" in source
            or "AsyncSessionLocal" in source
        ):
            violations.append(str(path.relative_to(backend_root)))

    assert violations == []


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
        "app/shared",
        "app/modules/submissions",
    ]

    remaining = [path for path in legacy_paths if (backend_root / path).exists()]
    assert remaining == []


def test_removed_compatibility_packages_are_absent() -> None:
    assert importlib.util.find_spec("app.shared") is None
    assert importlib.util.find_spec("app.modules.submissions") is None


def test_removed_runtime_aliases_are_absent() -> None:
    platform_config = importlib.import_module("app.platform.config")
    evaluator_registry = importlib.import_module(
        "app.worker.analysis.evaluator_registry"
    )

    assert not hasattr(platform_config.settings, "CREDENTIAL_STORAGE_DIR")
    assert not hasattr(evaluator_registry, "EVALUATORS")


def test_auth_dependency_and_runtime_rule_boundaries() -> None:
    assert importlib.util.find_spec("app.modules.auth.dependencies") is not None

    auth_module = importlib.import_module("app.platform.auth")
    assert hasattr(auth_module, "get_db")
    assert not hasattr(auth_module, "get_current_user")

    runtime_rules_module = importlib.import_module("app.platform.runtime_rules")
    assert hasattr(runtime_rules_module, "difficulty_bucket_bounds")
    assert hasattr(runtime_rules_module, "is_valid_request_id")
    assert not hasattr(runtime_rules_module, "build_controls")
    assert not hasattr(runtime_rules_module, "apply_pause_timeout")
    assert not hasattr(runtime_rules_module, "TERMINAL_STATUSES")


def test_worker_refactor_boundaries() -> None:
    assert importlib.util.find_spec("app.worker.runner") is None
    assert importlib.util.find_spec("app.worker.processing") is None
    assert importlib.util.find_spec("app.worker.claims") is None
    assert importlib.util.find_spec("app.worker.execution") is not None
    assert importlib.util.find_spec("app.worker.sample_scheduler") is not None
    assert importlib.util.find_spec("app.worker.sample_worker") is not None
