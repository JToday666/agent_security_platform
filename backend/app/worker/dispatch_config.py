"""Helpers for resolving per-run sample dispatch configuration."""

from __future__ import annotations

from typing import Protocol

from app.platform.config import settings


class RunDispatchSnapshot(Protocol):
    """Small protocol for objects carrying run dispatch metadata."""

    public_id: str
    execution_config: dict[str, object]


def resolve_timeout_seconds(run: RunDispatchSnapshot) -> int:
    """Derive runtime timeout from the saved execution config."""
    parameters = (
        run.execution_config.get("parameters")
        if isinstance(run.execution_config, dict)
        else {}
    )
    timeout_minutes = (
        parameters.get("timeoutMinutes") if isinstance(parameters, dict) else None
    )
    if isinstance(timeout_minutes, (int, float)) and timeout_minutes > 0:
        return max(1, int(timeout_minutes * 60))
    return settings.WORKER_EXECUTION_TIMEOUT_SECONDS


def resolve_dispatch_mode(run: RunDispatchSnapshot) -> str:
    """Resolve the worker dispatch mode for this run."""
    dispatch = (
        run.execution_config.get("dispatch")
        if isinstance(run.execution_config, dict)
        else None
    )
    if isinstance(dispatch, dict):
        mode = str(dispatch.get("mode") or "").strip().lower()
        if mode:
            return mode
    return settings.WORKER_DISPATCH_MODE_DEFAULT


def resolve_dispatch_config(run: RunDispatchSnapshot) -> dict[str, object]:
    """Build dispatch config passed to runtime adapters."""
    execution_config = run.execution_config if isinstance(run.execution_config, dict) else {}
    parameters = (
        execution_config.get("parameters")
        if isinstance(execution_config.get("parameters"), dict)
        else {}
    )
    config: dict[str, object] = {
        "evaluationId": run.public_id,
        "maxSteps": (
            parameters.get("maxSteps") if isinstance(parameters, dict) else None
        ),
    }
    frozen_agent_snapshot = execution_config.get("frozenAgentSnapshot")
    if isinstance(frozen_agent_snapshot, dict):
        config["frozenAgentSnapshot"] = frozen_agent_snapshot
    return config

