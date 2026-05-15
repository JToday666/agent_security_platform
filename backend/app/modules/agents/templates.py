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
            "connection": {
                "baseUrl": "",
                "invokePath": "/api/runs",
                "resultPathTemplate": "/api/runs/{externalRunId}",
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
    }
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
