"""Operator-facing lightweight health and worker status endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import get_current_user
from app.modules.ops.service import build_worker_status
from app.platform.auth import get_db
from app.platform.errors import ForbiddenError
from app.platform.http import success_payload
from app.platform.schemas import Envelope

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/workers", response_model=Envelope[dict[str, Any]])
async def get_workers_status(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return scheduler/sample-worker heartbeat state and queue counters."""
    if not getattr(current_user, "is_superuser", False):
        raise ForbiddenError("需要管理员权限。")
    return success_payload(await build_worker_status(db))

