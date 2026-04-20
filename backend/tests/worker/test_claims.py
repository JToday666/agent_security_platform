from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.worker import claims


pytestmark = pytest.mark.worker


def test_claim_is_stale_uses_heartbeat_timeout() -> None:
    stale_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    fresh_at = datetime.now(timezone.utc) - timedelta(seconds=10)

    assert claims.claim_is_stale(stale_at, stale_after_seconds=30) is True
    assert claims.claim_is_stale(fresh_at, stale_after_seconds=30) is False
    assert claims.claim_is_stale(None, stale_after_seconds=30) is False

