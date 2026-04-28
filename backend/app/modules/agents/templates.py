"""Built-in Agent registration templates."""

from app.modules.agents.schemas import AgentTemplate


TEMPLATES = [
    AgentTemplate.model_validate(
        {
            "templateId": "http_submit_poll_basic",
            "name": "提交 + 轮询 Agent",
            "description": "适用于先提交任务，再通过运行 ID 轮询结果的 Agent。",
            "recommended": True,
            "sortOrder": 10,
            "level": "basic",
            "tags": ["推荐", "异步", "轮询"],
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
                "requestOptions": {"structuredOutput": {"supported": True, "fieldAlias": "outputSchema"}},
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
    )
]


def list_agent_templates() -> list[AgentTemplate]:
    """Return built-in templates sorted for display."""
    return sorted(TEMPLATES, key=lambda template: template.sort_order)
