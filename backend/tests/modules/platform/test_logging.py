from __future__ import annotations

import json
import logging


def test_json_formatter_renders_extra_fields_and_redacts_secrets() -> None:
    from app.platform.logging import JsonLogFormatter

    record = logging.LogRecord(
        name="app.tests",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="agent_call_finished",
        args=(),
        exc_info=None,
    )
    record.service = "backend-api"
    record.event = "agent.dispatch.finished"
    record.requestId = "req_test"
    record.Authorization = "Bearer raw-secret"
    record.payload = {
        "api_key": "sk-raw-secret",
        "nested": {"token": "runtime-token", "value": "safe"},
    }

    payload = json.loads(JsonLogFormatter(env="test").format(record))

    assert payload["level"] == "INFO"
    assert payload["service"] == "backend-api"
    assert payload["env"] == "test"
    assert payload["event"] == "agent.dispatch.finished"
    assert payload["requestId"] == "req_test"
    assert payload["message"] == "agent_call_finished"
    assert payload["Authorization"] == "[REDACTED]"
    assert payload["payload"]["api_key"] == "[REDACTED]"
    assert payload["payload"]["nested"]["token"] == "[REDACTED]"
    assert payload["payload"]["nested"]["value"] == "safe"
    assert "raw-secret" not in json.dumps(payload)


def test_sanitize_url_removes_sensitive_query_values() -> None:
    from app.platform.logging import sanitize_for_log

    sanitized = sanitize_for_log(
        {
            "url": (
                "https://api.example.com/run?token=runtime-secret"
                "&trace=abc&api_key=key-secret"
            )
        }
    )

    assert sanitized["url"] == (
        "https://api.example.com/run?token=%5BREDACTED%5D"
        "&trace=abc&api_key=%5BREDACTED%5D"
    )


def test_sanitize_text_redacts_common_secret_shapes() -> None:
    from app.platform.logging import sanitize_for_log

    sanitized = sanitize_for_log(
        "Authorization: Bearer raw-token password=raw-password "
        "postgresql://user:raw-db-password@localhost/db"
    )

    assert "raw-token" not in sanitized
    assert "raw-password" not in sanitized
    assert "raw-db-password" not in sanitized
    assert "[REDACTED]" in sanitized


def test_json_formatter_normalizes_common_field_names_and_drops_noise() -> None:
    from app.platform.logging import JsonLogFormatter

    record = logging.LogRecord(
        name="uvicorn.error",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Started server process [1]",
        args=(),
        exc_info=None,
    )
    record.run_id = 12
    record.sample_execution_id = 34
    record.status_code = 200
    record.latency_ms = 9
    record.error_class = "RuntimeError"
    record.color_message = "Started server process [\u001b[36m1\u001b[0m]"

    payload = json.loads(JsonLogFormatter(env="test").format(record))

    assert payload["runId"] == 12
    assert payload["sampleExecutionId"] == 34
    assert payload["statusCode"] == 200
    assert payload["durationMs"] == 9
    assert payload["errorClass"] == "RuntimeError"
    assert "color_message" not in payload
    assert "latency_ms" not in payload
