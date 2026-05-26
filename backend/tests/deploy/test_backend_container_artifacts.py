from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"
BACKEND_TEMPLATE_ROOT = REPO_ROOT / "docs" / "deploy" / "templates" / "backend"


def _service_section(compose_text: str, service_name: str) -> str:
    marker = f"  {service_name}:"
    start = compose_text.index(marker)
    next_start = compose_text.find("\n  backend-", start + len(marker))
    if next_start == -1:
        next_start = compose_text.find("\nnetworks:", start + len(marker))
    return compose_text[start:next_start]


def test_backend_dockerfile_builds_single_runtime_image() -> None:
    dockerfile = (BACKEND_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "ARG DOCKER_CLI_IMAGE=docker:29-cli" in dockerfile
    assert "FROM ${DOCKER_CLI_IMAGE} AS docker-cli" in dockerfile
    assert "ARG BASE_IMAGE=python:3.12-slim" in dockerfile
    assert "FROM ${BASE_IMAGE}" in dockerfile
    assert dockerfile.index("ARG BASE_IMAGE=python:3.12-slim") < dockerfile.index(
        "FROM ${DOCKER_CLI_IMAGE} AS docker-cli"
    )
    assert "WORKDIR /app" in dockerfile
    assert "COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker" in dockerfile
    assert "http://mirrors.aliyun.com/debian" in dockerfile
    assert "http://mirrors.aliyun.com/debian-security" in dockerfile
    assert "PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple" in dockerfile
    assert "PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn" in dockerfile
    assert "pip install" in dockerfile
    assert "requirements.txt" in dockerfile
    assert "docker.io" not in dockerfile
    assert "COPY . ." in dockerfile
    assert 'CMD ["uvicorn", "app.main:app"' in dockerfile


def test_backend_dockerignore_excludes_local_state_and_tests() -> None:
    dockerignore = (BACKEND_ROOT / ".dockerignore").read_text(encoding="utf-8")

    for pattern in (".env", ".venv", ".pytest_cache", "__pycache__", "tests/"):
        assert pattern in dockerignore


def test_backend_compose_defines_phase1_services_with_same_image() -> None:
    compose = (
        BACKEND_TEMPLATE_ROOT / "docker-compose.backend.yml"
    ).read_text(encoding="utf-8")

    for service in (
        "backend-migrate",
        "backend-api",
        "backend-scheduler",
        "backend-worker",
    ):
        section = _service_section(compose, service)
        assert "image: ${BACKEND_IMAGE:?set BACKEND_IMAGE}" in section
        assert "env_file:" in section
        assert "/data/agent-security-platform/env/prod/backend.env" in section

    assert 'command: ["alembic", "upgrade", "head"]' in _service_section(
        compose, "backend-migrate"
    )
    assert 'command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]' in _service_section(
        compose, "backend-api"
    )
    assert 'command: ["python", "scheduler.py"]' in _service_section(
        compose, "backend-scheduler"
    )
    assert 'command: ["python", "worker.py"]' in _service_section(
        compose, "backend-worker"
    )


def test_backend_compose_overrides_container_runtime_addresses() -> None:
    compose = (
        BACKEND_TEMPLATE_ROOT / "docker-compose.backend.yml"
    ).read_text(encoding="utf-8")

    for service in (
        "backend-migrate",
        "backend-api",
        "backend-scheduler",
        "backend-worker",
    ):
        section = _service_section(compose, service)
        assert "DATABASE_URL: ${BACKEND_DATABASE_URL:?set BACKEND_DATABASE_URL}" in section

    for service in ("backend-api", "backend-worker"):
        section = _service_section(compose, service)
        assert "LLM_BASE_URL: ${BACKEND_LLM_BASE_URL:-http://asp-litellm:4000/v1}" in section

    api = _service_section(compose, "backend-api")
    assert "FASTAPI_HOST: 0.0.0.0" in api
    assert "FASTAPI_PORT: 8000" in api

    worker = _service_section(compose, "backend-worker")
    assert "WORKER_RUNTIME_LAUNCH_MODE: docker" in worker
    assert "WORKER_RUNTIME_DOCKER_NETWORK: asp-runtime-net" in worker
    assert "WORKER_RUNTIME_DOCKER_PORT: 8000" in worker


def test_only_backend_worker_mounts_docker_socket() -> None:
    compose = (
        BACKEND_TEMPLATE_ROOT / "docker-compose.backend.yml"
    ).read_text(encoding="utf-8")

    worker = _service_section(compose, "backend-worker")
    assert "/var/run/docker.sock:/var/run/docker.sock" in worker

    for service in ("backend-migrate", "backend-api", "backend-scheduler"):
        assert "/var/run/docker.sock" not in _service_section(compose, service)


def test_backend_compose_network_boundaries_are_explicit() -> None:
    compose = (
        BACKEND_TEMPLATE_ROOT / "docker-compose.backend.yml"
    ).read_text(encoding="utf-8")

    migrate = _service_section(compose, "backend-migrate")
    api = _service_section(compose, "backend-api")
    scheduler = _service_section(compose, "backend-scheduler")
    worker = _service_section(compose, "backend-worker")

    assert "- asp-db-net" in migrate
    assert "- asp-net" in api
    assert "- asp-db-net" in api
    assert "- asp-ai-net" in api
    assert "- asp-db-net" in scheduler
    assert "- asp-ai-net" not in scheduler
    assert "- asp-runtime-net" not in scheduler
    assert "- asp-db-net" in worker
    assert "- asp-ai-net" in worker
    assert "- asp-runtime-net" in worker

    for network in ("asp-net", "asp-db-net", "asp-ai-net", "asp-runtime-net"):
        assert f"  {network}:" in compose
        assert "external: true" in compose[compose.index(f"  {network}:") :]


def test_backend_prod_env_template_uses_container_network_addresses() -> None:
    env_template = (
        BACKEND_TEMPLATE_ROOT / "backend.env.example"
    ).read_text(encoding="utf-8")

    assert "FASTAPI_HOST=0.0.0.0" in env_template
    assert "@asp-postgres:5432/asp_db" in env_template
    assert "LLM_BASE_URL=http://asp-litellm:4000/v1" in env_template
    assert "WORKER_RUNTIME_LAUNCH_MODE=docker" in env_template
    assert "WORKER_RUNTIME_DOCKER_IMAGE=<provided-by-compose-BACKEND_IMAGE>" in env_template
    assert "WORKER_RUNTIME_DOCKER_NETWORK=asp-runtime-net" in env_template
    assert "WORKER_RUNTIME_DOCKER_PORT=8000" in env_template
    assert "PUBLIC_BASE_URL=https://<domain>" in env_template
    assert "RUNTIME_SESSION_TTL_SECONDS=900" in env_template
    assert "RUNTIME_GATEWAY_COOKIE_NAME=asp_runtime_token" in env_template
    assert "RUNTIME_REAPER_INTERVAL_SECONDS=30" in env_template
    assert "RUNTIME_CONTAINER_REAPER_ENABLED=true" in env_template


def test_backend_compose_env_template_uses_immutable_image_and_network_db_url() -> None:
    compose_env = (
        BACKEND_TEMPLATE_ROOT / "compose.env.example"
    ).read_text(encoding="utf-8")

    assert "BACKEND_IMAGE=" in compose_env
    assert "backend-<git-sha>" in compose_env
    assert "BACKEND_DATABASE_URL=postgresql+psycopg://asp_app:<password>@asp-postgres:5432/asp_db" in compose_env
    assert "BACKEND_LLM_BASE_URL=http://asp-litellm:4000/v1" in compose_env


def test_gateway_documentation_routes_runtime_tasks_to_backend_api() -> None:
    implementation_doc = (
        REPO_ROOT / "docs" / "deploy" / "02-deployment-implementation.md"
    ).read_text(encoding="utf-8")

    assert "handle /runtime/tasks/*" in implementation_doc
    assert "reverse_proxy backend-api:8000" in implementation_doc
    assert "location /runtime/tasks/" in implementation_doc
    assert "proxy_pass http://backend-api:8000" in implementation_doc


def test_operations_runbook_documents_runtime_gateway_cleanup_and_verification() -> None:
    runbook = (
        REPO_ROOT / "docs" / "deploy" / "03-operations-runbook.md"
    ).read_text(encoding="utf-8")

    assert "runtime session reaper" in runbook
    assert "managedBy=asp-worker" in runbook
    assert "/runtime/tasks/" in runbook
    assert "token" in runbook
