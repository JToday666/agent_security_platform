from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app.modules.agents.invocation import AgentInvocationClient, AgentInvocationResult
from app.platform.credentials import FileCredentialStore


def test_agent_templates_include_browser_use_output_and_render_contract(client) -> None:
    response = client.get("/api/v1/agents/templates")
    assert response.status_code == 200
    templates = {
        item["templateId"]: item["defaultConfig"] for item in response.json()["data"]
    }

    assert (
        templates["browser_use_cloud_v2_tasks"]["platformOutputMapping"]["success"]
        == "isSuccess"
    )
    assert (
        templates["browser_use_cloud_v3_sessions"]["platformOutputMapping"]["success"]
        == "isTaskSuccessful"
    )
    assert (
        templates["browser_use_cloud_v3_sessions"]["taskRenderMode"]
        == "goal_with_entry_url"
    )


@pytest.mark.db
@pytest.mark.integration
def test_agent_and_evaluation_submission_routes_work_against_real_database(
    client, api_db_helper, monkeypatch, backend_root: Path
) -> None:
    dataset_code = api_db_helper.seed_dataset()
    user_id, token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_submitter",
        email=f"{api_db_helper.prefix}_submit@example.com",
    )
    assert user_id > 0
    headers = {"Authorization": f"Bearer {token}"}

    async def fake_invoke(self, *, agent_snapshot, credential_payload, platform_values):
        return AgentInvocationResult(
            passed=True,
            status="completed",
            external_run_id="verify_run",
            final_answer="ok",
            error_message=None,
            raw_response={"status": "completed", "answer": "ok"},
        )

    monkeypatch.setattr(AgentInvocationClient, "invoke", fake_invoke)
    credential_dir = (
        backend_root / "runtime" / "test-credentials" / api_db_helper.prefix
    )
    monkeypatch.setattr(
        "app.modules.agents.service.default_credential_store",
        lambda: FileCredentialStore(credential_dir, "pytest-secret-key"),
    )
    try:
        templates_response = client.get("/api/v1/agents/templates")
        assert templates_response.status_code == 200
        assert (
            templates_response.json()["data"][0]["templateId"]
            == "http_submit_poll_basic"
        )

        agent_payload = {
            "templateId": "http_submit_poll_basic",
            "name": f"{api_db_helper.prefix} agent",
            "description": "db smoke submit",
            "invokeMode": "sync_response",
            "connection": {
                "baseUrl": "https://agent.example.com",
                "invokePath": "/run",
                "requestTimeoutSeconds": 30,
            },
            "auth": {"type": "bearer", "config": {"token": "sk-smoke"}},
            "platformInputMapping": {
                "task": "prompt",
                "entryUrl": "url",
                "timeoutSeconds": "timeout_sec",
                "sampleId": "case_id",
                "evaluationId": "evaluation_id",
                "maxSteps": "max_steps",
            },
            "taskRenderMode": "goal_only",
            "customRequestBody": {"engine": "demo"},
            "requestOptions": {},
            "platformOutputMapping": {
                "status": "status",
                "finalAnswer": "answer",
                "errorMessage": "error",
            },
            "terminalStatuses": ["completed", "failed"],
            "successStatuses": ["completed"],
        }

        create_agent_response = client.post(
            "/api/v1/agents", headers=headers, json=agent_payload
        )
        assert create_agent_response.status_code == 200
        agent_id = create_agent_response.json()["data"]["agentId"]

        verify_response = client.post(
            f"/api/v1/agents/{agent_id}/verify",
            headers=headers,
            json={"timeoutSeconds": 30},
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["data"]["passed"] is True
        assert verify_response.json()["data"]["status"] == "active"

        detail_response = client.get(f"/api/v1/agents/{agent_id}", headers=headers)
        assert detail_response.status_code == 200
        detail = detail_response.json()["data"]
        assert detail["auth"]["hasCredential"] is True
        assert "token" not in detail["auth"]["publicConfig"]

        meta_response = client.get("/api/v1/evaluations/meta")
        assert meta_response.status_code == 200
        assert meta_response.json()["data"]["submitMethods"] == ["api"]
        assert meta_response.json()["data"]["maxSteps"] == {
            "min": 1,
            "max": 100,
            "step": 1,
            "default": 30,
        }
        assert meta_response.json()["data"]["leaderboardDisplayMode"] == {
            "default": "public",
            "options": ["public", "anonymous"],
        }

        payload = {
            "submitMethod": "api",
            "agentId": agent_id,
            "parameters": {
                "difficulty": 0.5,
                "timeoutMinutes": 20,
                "maxSteps": 30,
            },
            "leaderboardDisplayMode": "anonymous",
            "datasetIds": [dataset_code],
            "requestId": f"{api_db_helper.prefix}_request_001",
        }

        validate_response = client.post(
            "/api/v1/evaluations/validate", headers=headers, json=payload
        )
        assert validate_response.status_code == 200
        assert validate_response.json()["data"] == {
            "ok": True,
            "warnings": [
                {
                    "code": "PUBLIC_LEADERBOARD",
                    "message": "本次结果将进入公开排行榜，请确认描述中不包含敏感信息。",
                }
            ],
        }

        submit_response = client.post(
            "/api/v1/evaluations", headers=headers, json=payload
        )
        assert submit_response.status_code == 200
        first_submit = submit_response.json()["data"]
        assert first_submit["status"] == "pending"
        assert first_submit["submitMethod"] == "api"
        assert first_submit["agentId"] == agent_id

        repeat_submit_response = client.post(
            "/api/v1/evaluations", headers=headers, json=payload
        )
        assert repeat_submit_response.status_code == 200
        repeat_submit = repeat_submit_response.json()["data"]
        assert repeat_submit["evaluationId"] == first_submit["evaluationId"]
        assert repeat_submit["status"] == first_submit["status"]

        detail_response = client.get(
            f"/api/v1/evaluations/{first_submit['evaluationId']}",
            headers=headers,
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()["data"]
        assert detail["publicToLeaderboard"] is True
        assert detail["leaderboardDisplayMode"] == "anonymous"
        assert detail["startedAt"] is None
        assert detail["finishedAt"] is None
        assert detail["progress"]["totalSampleCount"] >= 1
        assert detail["progress"]["completedSampleCount"] == 0

        default_payload = {
            "submitMethod": "api",
            "agentId": agent_id,
            "parameters": {
                "difficulty": 0.5,
                "timeoutMinutes": 20,
                "maxSteps": 30,
            },
            "datasetIds": [dataset_code],
            "requestId": f"{api_db_helper.prefix}_request_002",
        }
        default_submit_response = client.post(
            "/api/v1/evaluations", headers=headers, json=default_payload
        )
        assert default_submit_response.status_code == 200
        default_detail_response = client.get(
            f"/api/v1/evaluations/{default_submit_response.json()['data']['evaluationId']}",
            headers=headers,
        )
        assert default_detail_response.status_code == 200
        assert (
            default_detail_response.json()["data"]["leaderboardDisplayMode"] == "public"
        )

        deprecated_payload = {
            **default_payload,
            "requestId": f"{api_db_helper.prefix}_request_003",
            "publicToLeaderboard": False,
        }
        deprecated_response = client.post(
            "/api/v1/evaluations", headers=headers, json=deprecated_payload
        )
        assert deprecated_response.status_code == 422
        assert deprecated_response.json()["code"] == 1000
    finally:
        shutil.rmtree(credential_dir, ignore_errors=True)
