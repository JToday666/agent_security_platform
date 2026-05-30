from __future__ import annotations

import logging


def test_api_request_logging_sets_request_id_and_redacts_query(client, caplog) -> None:
    caplog.set_level(logging.INFO, logger="app.platform.request_logging")

    response = client.get(
        "/healthz?token=runtime-secret",
        headers={"X-Request-ID": "req-from-test"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-from-test"

    record = next(
        item for item in caplog.records if item.message == "http.request.completed"
    )
    assert record.requestId == "req-from-test"
    assert record.traceId == "req-from-test"
    assert record.event == "http.request.completed"
    assert record.path == "/healthz"
    assert record.query == "token=%5BREDACTED%5D"
    assert record.statusCode == 200
    assert isinstance(record.durationMs, int)
    assert "runtime-secret" not in record.query
