from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock, patch

import pytest

from app.platform.config import settings
from tests.helpers.api_db import png_bytes


@pytest.mark.db
@pytest.mark.integration
def test_auth_and_user_routes_work_against_real_database(client, api_db_helper) -> None:
    register_payload = {
        "username": f"{api_db_helper.prefix}_alice",
        "email": f"{api_db_helper.prefix}@example.com",
        "password": "secret123",
    }

    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 200
    token = register_response.json()["data"]["token"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": register_payload["username"],
            "password": register_payload["password"],
        },
    )
    assert login_response.status_code == 200
    assert login_response.json()["data"]["user"]["email"] == register_payload["email"]

    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["data"]["username"] == register_payload["username"]

    profile_response = client.get("/api/v1/user/profile", headers=headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["data"]["email"] == register_payload["email"]

    update_response = client.put(
        "/api/v1/user/profile",
        headers=headers,
        json={"username": f"{api_db_helper.prefix}_renamed"},
    )
    assert update_response.status_code == 200
    assert (
        update_response.json()["data"]["username"] == f"{api_db_helper.prefix}_renamed"
    )

    with TemporaryDirectory() as tmpdir:
        avatars_root = Path(tmpdir)
        with patch.object(
            type(settings),
            "avatars_root",
            new_callable=PropertyMock,
            return_value=avatars_root,
        ):
            avatar_response = client.post(
                "/api/v1/user/avatar",
                headers=headers,
                files={"avatar": ("avatar.png", png_bytes(), "image/png")},
            )
        assert avatar_response.status_code == 200
        avatar_url = avatar_response.json()["data"]["avatarUrl"]
        assert avatar_url.startswith("/uploads/avatars/")
        assert (avatars_root / avatar_url.rsplit("/", 1)[-1]).exists()

    unauthorized_response = client.get("/api/v1/user/profile")
    assert unauthorized_response.status_code == 401
    assert unauthorized_response.json()["code"] == 40100
