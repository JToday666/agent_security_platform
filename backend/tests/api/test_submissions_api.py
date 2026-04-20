from __future__ import annotations

import pytest


@pytest.mark.db
@pytest.mark.integration
def test_submission_routes_work_against_real_database(client, api_db_helper) -> None:
    dataset_code = api_db_helper.seed_dataset()
    user_id, token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_submitter",
        email=f"{api_db_helper.prefix}_submit@example.com",
    )
    assert user_id > 0
    headers = {"Authorization": f"Bearer {token}"}

    submit_meta_response = client.get("/api/v1/agents/submit-meta")
    assert submit_meta_response.status_code == 200
    assert submit_meta_response.json()["data"]["supportedMethods"] == ["api", "docker"]

    payload = {
        "agentName": f"{api_db_helper.prefix} agent",
        "description": "db smoke submit",
        "submitMethod": "api",
        "api": {
            "baseUrl": "https://example.com/agent",
            "token": "sk-smoke",
        },
        "parameters": {
            "difficulty": 0.5,
            "timeoutMinutes": 20,
            "retryEnabled": False,
        },
        "publicToLeaderboard": False,
        "datasetIds": [dataset_code],
        "requestId": f"{api_db_helper.prefix}_request_001",
    }

    precheck_response = client.post("/api/v1/agents/precheck", headers=headers, json=payload)
    assert precheck_response.status_code == 200
    assert precheck_response.json()["data"] == {"ok": True, "warnings": []}

    submit_response = client.post("/api/v1/agents/submit", headers=headers, json=payload)
    assert submit_response.status_code == 200
    first_submit = submit_response.json()["data"]
    assert first_submit["status"] == "pending"

    repeat_submit_response = client.post("/api/v1/agents/submit", headers=headers, json=payload)
    assert repeat_submit_response.status_code == 200
    repeat_submit = repeat_submit_response.json()["data"]
    assert repeat_submit["evaluationId"] == first_submit["evaluationId"]
    assert repeat_submit["status"] == first_submit["status"]
