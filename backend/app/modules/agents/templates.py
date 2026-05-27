"""Built-in Agent registration templates."""

from typing import Any

from app.modules.agents.schemas import AgentTemplate
from app.platform.i18n import translate

TEMPLATES: list[dict[str, Any]] = [
    {
        "templateId": "http_submit_poll_basic",
        "nameKey": "agents.templates.submit_poll_basic.name",
        "descriptionKey": "agents.templates.submit_poll_basic.description",
        "recommended": True,
        "sortOrder": 10,
        "level": "basic",
        "tagKeys": [
            "agents.templates.tags.recommended",
            "agents.templates.tags.async",
            "agents.templates.tags.polling",
        ],
        "defaultConfig": {
            "invokeMode": "submit_poll",
            "maxConcurrency": 4,
            "connection": {
                "baseUrl": "",
                "invokePath": "/api/runs",
                "resultPathTemplate": "/api/runs/{externalRunId}",
                "cancelPathTemplate": None,
                "cancelMethod": "POST",
                "cancelRequestBody": None,
                "requestTimeoutSeconds": 30,
                "pollIntervalSeconds": 2,
                "pollTimeoutSeconds": 300,
            },
            "auth": {"type": "bearer", "config": {"token": ""}},
            "platformInputMapping": {
                "task": "task",
                "entryUrl": "entryUrl",
                "timeoutSeconds": "timeoutSeconds",
                "sampleId": "sampleId",
                "evaluationId": "evaluationId",
                "maxSteps": "maxSteps",
            },
            "taskRenderMode": "goal_only",
            "customRequestBody": {},
            "requestOptions": {
                "structuredOutput": {"supported": True, "fieldAlias": "outputSchema"}
            },
            "platformOutputMapping": {
                "externalRunId": "data.runId",
                "status": "data.status",
                "finalAnswer": "data.answer",
                "errorMessage": "data.error.message",
                "stepCount": "data.metrics.stepCount",
                "artifacts": "data.artifacts",
            },
            "terminalStatuses": ["completed", "failed", "timed_out"],
            "successStatuses": ["completed"],
        },
    },
    {
        "templateId": "skyvern_cloud_api",
        "nameKey": "agents.templates.skyvern_cloud.name",
        "descriptionKey": "agents.templates.skyvern_cloud.description",
        "recommended": False,
        "sortOrder": 20,
        "level": "cloud",
        "tagKeys": [
            "agents.templates.tags.cloud_api",
            "agents.templates.tags.browser_automation",
            "agents.templates.tags.skyvern",
        ],
        "defaultConfig": {
            "invokeMode": "submit_poll",
            "maxConcurrency": 4,
            "connection": {
                "baseUrl": "https://api.skyvern.com",
                "invokePath": "/v1/run/tasks",
                "resultPathTemplate": "/v1/runs/{externalRunId}",
                "cancelPathTemplate": "/v1/runs/{externalRunId}/cancel",
                "cancelMethod": "POST",
                "cancelRequestBody": None,
                "requestTimeoutSeconds": 30,
                "pollIntervalSeconds": 2,
                "pollTimeoutSeconds": 900,
            },
            "auth": {
                "type": "api_key_header",
                "config": {"headerName": "x-api-key", "secret": ""},
            },
            "platformInputMapping": {
                "task": "prompt",
                "entryUrl": "url",
                "maxSteps": "max_steps",
            },
            "taskRenderMode": "goal_only",
            "customRequestBody": {"engine": "skyvern-2.0"},
            "requestOptions": {
                "structuredOutput": {
                    "supported": True,
                    "fieldAlias": "data_extraction_schema",
                }
            },
            "platformOutputMapping": {
                "externalRunId": "run_id",
                "status": "status",
                "finalAnswer": "output",
                "errorMessage": "failure_reason",
            },
            "terminalStatuses": [
                "completed",
                "failed",
                "timed_out",
                "terminated",
                "canceled",
            ],
            "successStatuses": ["completed"],
        },
    },
    {
        "templateId": "browser_use_cloud_v2_tasks",
        "nameKey": "agents.templates.browser_use_v2_tasks.name",
        "descriptionKey": "agents.templates.browser_use_v2_tasks.description",
        "recommended": False,
        "sortOrder": 30,
        "level": "cloud",
        "tagKeys": [
            "agents.templates.tags.cloud_api",
            "agents.templates.tags.browser_automation",
            "agents.templates.tags.browser_use",
            "agents.templates.tags.v2",
        ],
        "defaultConfig": {
            "invokeMode": "submit_poll",
            "maxConcurrency": 4,
            "connection": {
                "baseUrl": "https://api.browser-use.com/api/v2",
                "invokePath": "/tasks",
                "resultPathTemplate": "/tasks/{externalRunId}/status",
                "cancelPathTemplate": "/tasks/{externalRunId}",
                "cancelMethod": "PATCH",
                "cancelRequestBody": {"action": "stop_task_and_session"},
                "requestTimeoutSeconds": 30,
                "pollIntervalSeconds": 2,
                "pollTimeoutSeconds": 900,
            },
            "auth": {
                "type": "api_key_header",
                "config": {
                    "headerName": "X-Browser-Use-API-Key",
                    "secret": "",
                },
            },
            "platformInputMapping": {
                "task": "task",
                "entryUrl": "startUrl",
                "maxSteps": "maxSteps",
            },
            "taskRenderMode": "goal_only",
            "customRequestBody": {},
            "requestOptions": {
                "structuredOutput": {
                    "supported": True,
                    "fieldAlias": "structuredOutput",
                }
            },
            "platformOutputMapping": {
                "externalRunId": "id",
                "status": "status",
                "success": "isSuccess",
                "finalAnswer": "output",
                "errorMessage": "output",
            },
            "terminalStatuses": ["finished", "failed", "stopped"],
            "successStatuses": ["finished"],
        },
    },
    {
        "templateId": "browser_use_cloud_v3_sessions",
        "nameKey": "agents.templates.browser_use_v3_sessions.name",
        "descriptionKey": "agents.templates.browser_use_v3_sessions.description",
        "recommended": False,
        "sortOrder": 40,
        "level": "cloud",
        "tagKeys": [
            "agents.templates.tags.cloud_api",
            "agents.templates.tags.browser_automation",
            "agents.templates.tags.browser_use",
            "agents.templates.tags.v3",
        ],
        "defaultConfig": {
            "invokeMode": "submit_poll",
            "maxConcurrency": 4,
            "connection": {
                "baseUrl": "https://api.browser-use.com/api/v3",
                "invokePath": "/sessions",
                "resultPathTemplate": "/sessions/{externalRunId}",
                "cancelPathTemplate": "/sessions/{externalRunId}",
                "cancelMethod": "DELETE",
                "cancelRequestBody": None,
                "requestTimeoutSeconds": 30,
                "pollIntervalSeconds": 2,
                "pollTimeoutSeconds": 900,
            },
            "auth": {
                "type": "api_key_header",
                "config": {
                    "headerName": "X-Browser-Use-API-Key",
                    "secret": "",
                },
            },
            "platformInputMapping": {"task": "task"},
            "taskRenderMode": "goal_with_entry_url",
            "customRequestBody": {},
            "requestOptions": {
                "structuredOutput": {
                    "supported": True,
                    "fieldAlias": "outputSchema",
                }
            },
            "platformOutputMapping": {
                "externalRunId": "id",
                "status": "status",
                "success": "isTaskSuccessful",
                "finalAnswer": "output",
                "errorMessage": "lastStepSummary",
            },
            "terminalStatuses": ["stopped", "timed_out", "error"],
            "successStatuses": ["stopped"],
        },
    },
]


def _localized_template(template: dict[str, Any]) -> AgentTemplate:
    payload = dict(template)
    name_key = payload.pop("nameKey")
    description_key = payload.pop("descriptionKey")
    tag_keys = payload.pop("tagKeys")
    payload["name"] = translate(name_key)
    payload["description"] = translate(description_key)
    payload["tags"] = [translate(key) for key in tag_keys]
    return AgentTemplate.model_validate(payload)


def list_agent_templates() -> list[AgentTemplate]:
    """Return built-in templates sorted for display."""
    return [
        _localized_template(template)
        for template in sorted(
            TEMPLATES, key=lambda template: int(template["sortOrder"])
        )
    ]
