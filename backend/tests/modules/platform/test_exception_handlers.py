from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.platform.exception_handlers import register_exception_handlers


def test_unhandled_exception_is_logged_with_request_context(caplog) -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("database password should not leak")

    caplog.set_level(logging.ERROR, logger="app.platform.exception_handlers")
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/boom")

    assert response.status_code == 500
    record = next(
        item for item in caplog.records if item.message == "http.unhandled_exception"
    )
    assert record.event == "http.unhandled_exception"
    assert record.errorClass == "RuntimeError"
