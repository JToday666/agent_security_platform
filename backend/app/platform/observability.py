"""Helpers for sample execution events and audit logs."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, SampleExecutionEvent
from app.platform.db.session import AsyncSessionLocal
from app.platform.logging import current_log_context, sanitize_for_log

MAX_EVENT_PAYLOAD_KEYS = 40


class SampleExecutionEventType(str, Enum):
    """Allowed sample execution timeline event types."""

    EVALUATION_CREATED = "evaluation.created"
    EVALUATION_COMPLETED = "evaluation.completed"
    EVALUATION_FAILED = "evaluation.failed"
    EVALUATION_CANCELLED = "evaluation.cancelled"
    EVALUATION_TERMINATED = "evaluation.terminated"
    SAMPLE_CLAIMED = "sample.claimed"
    SAMPLE_EXECUTION_STARTED = "sample.execution.started"
    SAMPLE_EXECUTION_FAILED = "sample.execution.failed"
    SAMPLE_EXECUTION_FINISHED = "sample.execution.finished"
    SAMPLE_EXECUTION_CANCELLED = "sample.execution.cancelled"
    SAMPLE_EXECUTION_TIMEOUT = "sample.execution.timeout"
    RUNTIME_SESSION_CREATED = "runtime.session.created"
    RUNTIME_ROUTE_BOUND = "runtime.route.bound"
    RUNTIME_SESSION_EXPIRED = "runtime.session.expired"
    RUNTIME_SESSION_DESTROYED = "runtime.session.destroyed"
    AGENT_DISPATCH_STARTED = "agent.dispatch.started"
    ORACLE_JUDGEMENT_FINISHED = "oracle.judgement.finished"
    ARTIFACT_PERSISTED = "artifact.persisted"


class AuditActorType(str, Enum):
    """Allowed actor types for audit logs."""

    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"
    WORKER = "worker"
    AGENT = "agent"
    API_KEY = "api_key"
    ANONYMOUS = "anonymous"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _bounded_payload(payload: dict[str, Any] | None) -> dict[str, object]:
    if not payload:
        return {}
    sanitized = sanitize_for_log(payload)
    if not isinstance(sanitized, dict):
        return {"value": sanitized}
    bounded = dict(list(sanitized.items())[:MAX_EVENT_PAYLOAD_KEYS])
    if len(sanitized) > MAX_EVENT_PAYLOAD_KEYS:
        bounded["truncated"] = True
    return bounded


async def record_sample_execution_event(
    db: AsyncSession,
    *,
    run_id: int,
    event_type: SampleExecutionEventType,
    sample_execution_id: int | None = None,
    sample_id: str | None = None,
    worker_id: str | None = None,
    runtime_session_id: str | None = None,
    level: str = "INFO",
    status: str | None = None,
    message: str | None = None,
    payload: dict[str, Any] | None = None,
) -> SampleExecutionEvent:
    """Append one lightweight sample execution timeline event."""
    event = SampleExecutionEvent(
        run_id=run_id,
        sample_execution_id=sample_execution_id,
        sample_id=sample_id,
        worker_id=worker_id,
        runtime_session_id=runtime_session_id,
        event_type=event_type.value,
        level=level.upper(),
        status=status,
        message=message,
        payload=_bounded_payload(payload),
        occurred_at=_now_utc(),
    )
    db.add(event)
    return event


async def record_sample_execution_event_once(
    *,
    run_id: int,
    event_type: SampleExecutionEventType,
    sample_execution_id: int | None = None,
    sample_id: str | None = None,
    worker_id: str | None = None,
    runtime_session_id: str | None = None,
    level: str = "INFO",
    status: str | None = None,
    message: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Append and commit one event outside an existing transaction."""
    async with AsyncSessionLocal() as db:
        await record_sample_execution_event(
            db,
            run_id=run_id,
            event_type=event_type,
            sample_execution_id=sample_execution_id,
            sample_id=sample_id,
            worker_id=worker_id,
            runtime_session_id=runtime_session_id,
            level=level,
            status=status,
            message=message,
            payload=payload,
        )
        await db.commit()


async def record_audit_log(
    db: AsyncSession,
    *,
    actor_type: AuditActorType,
    actor_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    result: str,
    request_id: str | None = None,
    trace_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditLog:
    """Append one audit log row to the current transaction."""
    context = current_log_context()
    entry = AuditLog(
        actor_type=actor_type.value,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
        request_id=request_id or context.get("requestId"),
        trace_id=trace_id or context.get("traceId"),
        ip_address=ip_address,
        user_agent=user_agent,
        payload=_bounded_payload(payload),
    )
    db.add(entry)
    return entry
