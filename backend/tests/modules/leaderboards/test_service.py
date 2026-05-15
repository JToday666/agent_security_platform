from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from app.modules.leaderboards.service import _snapshot_response
from app.platform.i18n import set_current_locale


def test_snapshot_response_localizes_anonymous_display_name() -> None:
    snapshot = SimpleNamespace(snapshot_code="lb_demo")
    entry = SimpleNamespace(
        rank_no=1,
        display_name="Anonymous Agent",
        anonymous=True,
        official_conservative_score=Decimal("91.2"),
        safe_capability_score=Decimal("90.0"),
        high_difficulty_score=Decimal("82.5"),
        unsafe_risk_score=Decimal("3.0"),
        confidence=Decimal("0.9"),
        verification_tier="verified",
        safety_certification="certified",
        total_samples=12,
    )

    token = set_current_locale("ja-JP")
    try:
        response = _snapshot_response(snapshot, [entry])
    finally:
        token.reset()

    assert response.entries[0].display_name == "匿名 Agent"
