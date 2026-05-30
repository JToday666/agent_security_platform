from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.observability import AuditLog

pytestmark = [pytest.mark.db, pytest.mark.integration]


def test_auth_and_user_profile_actions_write_audit_logs(client, api_db_helper) -> None:
    username = f"{api_db_helper.prefix}_audit_user"
    email = f"{api_db_helper.prefix}_audit@example.com"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "secret123"},
    )
    assert register_response.status_code == 200
    session_data = register_response.json()["data"]
    user_id = session_data["user"]["id"]
    token = session_data["token"]

    failed_login_response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "wrong-secret"},
    )
    assert failed_login_response.status_code == 401

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    update_response = client.put(
        "/api/v1/user/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": f"{api_db_helper.prefix}_renamed_user"},
    )
    assert update_response.status_code == 200

    with api_db_helper.session() as session:
        rows = list(
            (
                session.execute(
                    select(AuditLog)
                    .where(AuditLog.actor_id == str(user_id))
                    .order_by(AuditLog.id)
                )
            ).scalars()
        )

    actions = [(row.action, row.result) for row in rows]
    assert ("auth.registered", "success") in actions
    assert ("auth.login", "failure") in actions
    assert ("auth.login", "success") in actions
    assert ("user.profile.updated", "success") in actions

    register_audit = next(row for row in rows if row.action == "auth.registered")
    failed_login_audit = next(
        row for row in rows if row.action == "auth.login" and row.result == "failure"
    )
    profile_audit = next(row for row in rows if row.action == "user.profile.updated")

    assert register_audit.payload == {"username": username}
    assert failed_login_audit.payload == {
        "reason": "invalid_credentials",
        "identifierType": "username",
    }
    assert profile_audit.payload == {"changedFields": ["username"]}
    assert "secret123" not in str([row.payload for row in rows])
