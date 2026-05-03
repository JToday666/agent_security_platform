from __future__ import annotations

from app.platform.runtime_rules import difficulty_bucket_bounds, is_valid_request_id


def test_request_id_validation() -> None:
    assert is_valid_request_id("submit_20260408_demo001") is True
    assert is_valid_request_id("A12345") is True
    assert is_valid_request_id("bad") is False
    assert is_valid_request_id("_submit_20260408_demo001") is False
    assert is_valid_request_id("submit 20260408 demo001") is False


def test_difficulty_bucket_bounds() -> None:
    assert difficulty_bucket_bounds(0) == (0.0, 0.05, False)
    assert difficulty_bucket_bounds(0.5) == (0.45, 0.55, False)
    assert difficulty_bucket_bounds(1) == (0.95, 1.0, True)
