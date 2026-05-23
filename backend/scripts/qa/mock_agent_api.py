"""Minimal local Agent API for external dispatch e2e runs."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

app = FastAPI(title="ASP Local Mock Agent")


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/run")
async def run(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "completed",
        "answer": {
            "receivedTask": payload.get("prompt"),
            "receivedUrl": payload.get("url"),
            "sampleId": payload.get("sample_id"),
            "evaluationId": payload.get("evaluation_id"),
        },
        "error": None,
    }
