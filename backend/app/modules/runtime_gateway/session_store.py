"""Runtime gateway session and token helpers."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RuntimeSession
from app.platform.config import settings
from app.platform.db.session import AsyncSessionLocal
from app.platform.observability import (
    SampleExecutionEventType,
    record_sample_execution_event,
)

RuntimeTokenSource = Literal[
    "query", "cookie", "missing", "invalid", "expired", "closed"
]


@dataclass(slots=True)
class RuntimeSessionView:
    """Runtime gateway session data needed by the public proxy route."""

    sample_execution_id: int
    internal_base_url: str
    public_entry_url: str
    token_hash: str
    expires_at: datetime
    status: str


@dataclass(slots=True)
class RuntimeSessionCreation:
    """Result returned to the worker after creating a runtime session."""

    token: str
    public_entry_url: str
    public_entry_url_without_token: str


def now_utc() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def generate_runtime_token() -> str:
    """Generate a high-entropy bearer token for one runtime session."""
    return secrets.token_urlsafe(32)


def hash_runtime_token(token: str) -> str:
    """Hash a runtime token before storing it."""
    digest = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256:{digest}"


def verify_runtime_token(token: str, token_hash: str) -> bool:
    """Return True when the plain token matches the stored hash."""
    if not token or not token_hash:
        return False
    return hmac.compare_digest(hash_runtime_token(token), token_hash)


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def runtime_session_is_active(session: RuntimeSessionView) -> bool:
    """Check status and expiry before allowing proxy access."""
    return session.status == "active" and _aware_utc(session.expires_at) > now_utc()


def _public_base_url() -> str:
    return str(settings.PUBLIC_BASE_URL or "http://127.0.0.1:8000").rstrip("/")


def build_public_runtime_url(
    *, sample_execution_id: int, internal_entry_url: str, token: str | None = None
) -> str:
    """Build the external URL delivered to browser-driving Agents."""
    parsed = urlsplit(internal_entry_url)
    entry_path = parsed.path or "/"
    public_path = f"/runtime/tasks/{sample_execution_id}{entry_path}"
    query_items = parse_qsl(parsed.query, keep_blank_values=True)
    if token is not None:
        query_items.append(("token", token))
    query = urlencode(query_items)
    public_url = f"{_public_base_url()}{public_path}"
    return f"{public_url}?{query}" if query else public_url


def _session_view(row: RuntimeSession) -> RuntimeSessionView:
    return RuntimeSessionView(
        sample_execution_id=row.sample_execution_id,
        internal_base_url=row.internal_base_url,
        public_entry_url=row.public_entry_url,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        status=row.status,
    )


async def create_runtime_session(
    *, prepared, run_id: int, timeout_seconds: int
) -> RuntimeSessionCreation:
    """Create or replace the gateway session for a launched runtime."""
    from app.worker.runtime.process import runtime_base_url

    token = generate_runtime_token()
    public_entry_url_without_token = build_public_runtime_url(
        sample_execution_id=prepared.execution_id,
        internal_entry_url=prepared.entry_url,
    )
    public_entry_url_with_token = build_public_runtime_url(
        sample_execution_id=prepared.execution_id,
        internal_entry_url=prepared.entry_url,
        token=token,
    )
    prepared.public_entry_url = public_entry_url_without_token
    prepared.public_entry_url_with_token = public_entry_url_with_token

    current_time = now_utc()
    expires_at = current_time + timedelta(
        seconds=max(int(timeout_seconds), int(settings.RUNTIME_SESSION_TTL_SECONDS))
    )
    internal_base_url = runtime_base_url(prepared).rstrip("/")

    async with AsyncSessionLocal() as db:
        existing = (
            await db.execute(
                select(RuntimeSession).where(
                    RuntimeSession.sample_execution_id == prepared.execution_id
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(
                RuntimeSession(
                    sample_execution_id=prepared.execution_id,
                    run_id=run_id,
                    environment_ref=prepared.environment_ref,
                    internal_base_url=internal_base_url,
                    public_entry_url=public_entry_url_without_token,
                    token_hash=hash_runtime_token(token),
                    expires_at=expires_at,
                    status="active",
                    revoked_at=None,
                    created_at=current_time,
                    updated_at=current_time,
                )
            )
        else:
            existing.run_id = run_id
            existing.environment_ref = prepared.environment_ref
            existing.internal_base_url = internal_base_url
            existing.public_entry_url = public_entry_url_without_token
            existing.token_hash = hash_runtime_token(token)
            existing.expires_at = expires_at
            existing.status = "active"
            existing.revoked_at = None
            existing.updated_at = current_time
        await record_sample_execution_event(
            db,
            run_id=run_id,
            sample_execution_id=prepared.execution_id,
            event_type=SampleExecutionEventType.RUNTIME_SESSION_CREATED,
            status="active",
            message="Runtime gateway session created",
            payload={
                "environmentRef": prepared.environment_ref,
                "publicEntryUrl": public_entry_url_without_token,
            },
        )
        await db.commit()

    return RuntimeSessionCreation(
        token=token,
        public_entry_url=public_entry_url_with_token,
        public_entry_url_without_token=public_entry_url_without_token,
    )


async def close_runtime_session(execution_id: int, *, status: str = "closed") -> None:
    """Revoke a runtime session after the sample reaches a terminal state."""
    current_time = now_utc()
    async with AsyncSessionLocal() as db:
        session = (
            await db.execute(
                select(RuntimeSession).where(
                    RuntimeSession.sample_execution_id == execution_id
                )
            )
        ).scalar_one_or_none()
        if session is None:
            return
        session.status = status
        session.revoked_at = current_time
        session.updated_at = current_time
        await record_sample_execution_event(
            db,
            run_id=session.run_id,
            sample_execution_id=session.sample_execution_id,
            event_type=SampleExecutionEventType.RUNTIME_SESSION_DESTROYED,
            status=status,
            message="Runtime gateway session closed",
            payload={"environmentRef": session.environment_ref},
        )
        await db.commit()


async def expire_runtime_sessions_once(
    db: AsyncSession, *, limit: int | None = None
) -> int:
    """Mark expired runtime sessions revoked without waiting for a gateway hit."""
    current_time = now_utc()
    stmt = (
        select(RuntimeSession)
        .where(
            RuntimeSession.status.in_(["preparing", "active"]),
            RuntimeSession.expires_at <= current_time,
        )
        .order_by(RuntimeSession.expires_at.asc(), RuntimeSession.id.asc())
        .with_for_update(skip_locked=True)
    )
    if limit is not None:
        stmt = stmt.limit(max(1, int(limit)))
    rows = list((await db.execute(stmt)).scalars())
    for row in rows:
        row.status = "expired"
        row.revoked_at = current_time
        row.updated_at = current_time
        await record_sample_execution_event(
            db,
            run_id=row.run_id,
            sample_execution_id=row.sample_execution_id,
            event_type=SampleExecutionEventType.RUNTIME_SESSION_EXPIRED,
            status="expired",
            message="Runtime gateway session expired",
            payload={"environmentRef": row.environment_ref},
        )
    await db.commit()
    return len(rows)


async def authorize_runtime_request(
    *,
    sample_execution_id: int,
    query_token: str | None,
    cookie_token: str | None,
) -> tuple[RuntimeSessionView | None, RuntimeTokenSource]:
    """Load a runtime session and validate the query token or scoped cookie."""
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(RuntimeSession).where(
                    RuntimeSession.sample_execution_id == sample_execution_id
                )
            )
        ).scalar_one_or_none()
        if row is None:
            return None, "missing"
        session = _session_view(row)
        if session.status not in {"preparing", "active"}:
            return None, "closed"
        if _aware_utc(session.expires_at) <= now_utc():
            row.status = "expired"
            row.revoked_at = now_utc()
            row.updated_at = now_utc()
            await db.commit()
            return None, "expired"
        token = query_token if query_token is not None else cookie_token
        source: RuntimeTokenSource = "query" if query_token is not None else "cookie"
        if not token:
            return None, "missing"
        if not verify_runtime_token(token, session.token_hash):
            return None, "invalid"
        if session.status != "active":
            return None, "closed"
        return session, source
