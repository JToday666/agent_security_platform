from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.models.user import User
from app.models.worker_process import WorkerProcess


def test_healthz_returns_alive(client) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


def test_readyz_returns_ready_when_database_is_available(client) -> None:
    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ready"


def test_ops_workers_requires_login(client) -> None:
    response = client.get("/api/v1/ops/workers")

    assert response.status_code == 401


def test_ops_workers_requires_superuser(client, api_db_helper) -> None:
    _, token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_ops_user",
        email=f"{api_db_helper.prefix}_ops_user@example.com",
    )

    response = client.get(
        "/api/v1/ops/workers",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_ops_workers_returns_worker_queue_and_alerts_for_superuser(
    client, api_db_helper
) -> None:
    user_id, token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_ops_admin",
        email=f"{api_db_helper.prefix}_ops_admin@example.com",
    )
    with api_db_helper.session() as session:
        user = session.get(User, user_id)
        user.is_superuser = True
        session.add(
            WorkerProcess(
                worker_id=f"{api_db_helper.prefix}_scheduler",
                role="scheduler",
                hostname="test-host",
                pid=123,
                status="healthy",
                started_at=datetime.now(timezone.utc),
                last_heartbeat_at=datetime.now(timezone.utc),
                active_count=0,
                process_metadata={"loopErrors": 0},
            )
        )
        session.commit()

    response = client.get(
        "/api/v1/ops/workers",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert any(
        worker["workerId"] == f"{api_db_helper.prefix}_scheduler"
        for worker in payload["workers"]
    )
    assert {"blocked", "ready", "claimed", "executing", "verifying", "done", "error"}.issubset(
        set(payload["sampleQueues"])
    )
    assert isinstance(payload["alerts"], list)
