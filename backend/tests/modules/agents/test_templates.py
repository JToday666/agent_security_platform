from __future__ import annotations

from app.modules.agents.templates import list_agent_templates


def _templates_by_id() -> dict[str, dict]:
    return {
        template.template_id: template.model_dump(by_alias=True)
        for template in list_agent_templates()
    }


def test_agent_templates_include_base_and_cloud_api_templates() -> None:
    templates = [template.model_dump(by_alias=True) for template in list_agent_templates()]

    assert [template["templateId"] for template in templates] == [
        "http_submit_poll_basic",
        "skyvern_cloud_api",
        "browser_use_cloud_v2_tasks",
        "browser_use_cloud_v3_sessions",
    ]
    assert [template["sortOrder"] for template in templates] == [10, 20, 30, 40]
    assert templates[0]["recommended"] is True
    assert all(template["recommended"] is False for template in templates[1:])


def test_skyvern_cloud_template_matches_official_task_api_shape() -> None:
    template = _templates_by_id()["skyvern_cloud_api"]
    config = template["defaultConfig"]

    assert config["connection"] == {
        "baseUrl": "https://api.skyvern.com",
        "invokePath": "/v1/run/tasks",
        "resultPathTemplate": "/v1/runs/{externalRunId}",
        "cancelPathTemplate": "/v1/runs/{externalRunId}/cancel",
        "cancelMethod": "POST",
        "cancelRequestBody": None,
        "requestTimeoutSeconds": 30,
        "pollIntervalSeconds": 2,
        "pollTimeoutSeconds": 900,
    }
    assert config["maxConcurrency"] == 4
    assert config["auth"] == {
        "type": "api_key_header",
        "config": {"headerName": "x-api-key", "secret": ""},
    }
    assert config["platformInputMapping"] == {
        "task": "prompt",
        "entryUrl": "url",
        "maxSteps": "max_steps",
    }
    assert config["platformOutputMapping"] == {
        "externalRunId": "run_id",
        "status": "status",
        "finalAnswer": "output",
        "errorMessage": "failure_reason",
    }
    assert config["terminalStatuses"] == [
        "completed",
        "failed",
        "timed_out",
        "terminated",
        "canceled",
    ]
    assert config["successStatuses"] == ["completed"]


def test_browser_use_cloud_templates_match_official_api_shapes() -> None:
    templates = _templates_by_id()
    v2_config = templates["browser_use_cloud_v2_tasks"]["defaultConfig"]
    v3_config = templates["browser_use_cloud_v3_sessions"]["defaultConfig"]

    assert v2_config["connection"] == {
        "baseUrl": "https://api.browser-use.com/api/v2",
        "invokePath": "/tasks",
        "resultPathTemplate": "/tasks/{externalRunId}/status",
        "cancelPathTemplate": "/tasks/{externalRunId}",
        "cancelMethod": "PATCH",
        "cancelRequestBody": {"action": "stop_task_and_session"},
        "requestTimeoutSeconds": 30,
        "pollIntervalSeconds": 2,
        "pollTimeoutSeconds": 900,
    }
    assert v2_config["auth"] == {
        "type": "api_key_header",
        "config": {"headerName": "X-Browser-Use-API-Key", "secret": ""},
    }
    assert v2_config["platformInputMapping"] == {
        "task": "task",
        "entryUrl": "startUrl",
        "maxSteps": "maxSteps",
    }
    assert v2_config["requestOptions"] == {
        "structuredOutput": {"supported": True, "fieldAlias": "structuredOutput"}
    }
    assert v2_config["platformOutputMapping"] == {
        "externalRunId": "id",
        "status": "status",
        "success": "isSuccess",
        "finalAnswer": "output",
        "errorMessage": "output",
    }
    assert v2_config["terminalStatuses"] == ["finished", "failed", "stopped"]
    assert v2_config["successStatuses"] == ["finished"]

    assert v3_config["connection"] == {
        "baseUrl": "https://api.browser-use.com/api/v3",
        "invokePath": "/sessions",
        "resultPathTemplate": "/sessions/{externalRunId}",
        "cancelPathTemplate": "/sessions/{externalRunId}",
        "cancelMethod": "DELETE",
        "cancelRequestBody": None,
        "requestTimeoutSeconds": 30,
        "pollIntervalSeconds": 2,
        "pollTimeoutSeconds": 900,
    }
    assert v2_config["maxConcurrency"] == 4
    assert v3_config["maxConcurrency"] == 4
    assert v3_config["auth"] == {
        "type": "api_key_header",
        "config": {"headerName": "X-Browser-Use-API-Key", "secret": ""},
    }
    assert v3_config["taskRenderMode"] == "goal_with_entry_url"
    assert v3_config["platformInputMapping"] == {
        "task": "task",
    }
    assert v3_config["requestOptions"] == {
        "structuredOutput": {"supported": True, "fieldAlias": "outputSchema"}
    }
    assert v3_config["platformOutputMapping"] == {
        "externalRunId": "id",
        "status": "status",
        "success": "isTaskSuccessful",
        "finalAnswer": "output",
        "errorMessage": "lastStepSummary",
    }
    assert v3_config["terminalStatuses"] == ["stopped", "timed_out", "error"]
    assert v3_config["successStatuses"] == ["stopped"]
