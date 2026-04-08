import unittest
from datetime import datetime, timedelta, timezone

from app.services.runtime_rules import (
    apply_pause_timeout,
    build_controls,
    difficulty_bucket_bounds,
    is_valid_request_id,
)


class RuntimeRulesTestCase(unittest.TestCase):
    def test_request_id_validation(self) -> None:
        self.assertTrue(is_valid_request_id("submit_20260408_demo001"))
        self.assertTrue(is_valid_request_id("A12345"))
        self.assertFalse(is_valid_request_id("bad"))
        self.assertFalse(is_valid_request_id("_submit_20260408_demo001"))
        self.assertFalse(is_valid_request_id("submit 20260408 demo001"))

    def test_difficulty_bucket_bounds(self) -> None:
        self.assertEqual(difficulty_bucket_bounds(0), (0.0, 0.05, False))
        self.assertEqual(difficulty_bucket_bounds(0.5), (0.45, 0.55, False))
        self.assertEqual(difficulty_bucket_bounds(1), (0.95, 1.0, True))

    def test_controls_for_running_and_paused_states(self) -> None:
        self.assertEqual(
            build_controls(status="running", pause_used=False),
            {
                "canPause": True,
                "canResume": False,
                "canTerminate": True,
                "canCancel": True,
                "pauseUsed": False,
            },
        )
        self.assertEqual(
            build_controls(status="paused", pause_used=True),
            {
                "canPause": False,
                "canResume": True,
                "canTerminate": True,
                "canCancel": True,
                "pauseUsed": True,
            },
        )

    def test_apply_pause_timeout_auto_terminates_expired_paused_run(self) -> None:
        expired_at = datetime.now(timezone.utc) - timedelta(minutes=1)

        status, finalization_reason, pause_deadline_at = apply_pause_timeout(
            status="paused",
            finalization_reason=None,
            pause_deadline_at=expired_at,
        )

        self.assertEqual(status, "terminated")
        self.assertEqual(finalization_reason, "auto_terminated_after_pause_timeout")
        self.assertIsNone(pause_deadline_at)

    def test_apply_pause_timeout_keeps_active_runs_unchanged(self) -> None:
        future_at = datetime.now(timezone.utc) + timedelta(minutes=1)

        status, finalization_reason, pause_deadline_at = apply_pause_timeout(
            status="running",
            finalization_reason=None,
            pause_deadline_at=future_at,
        )

        self.assertEqual(status, "running")
        self.assertIsNone(finalization_reason)
        self.assertEqual(pause_deadline_at, future_at)


if __name__ == "__main__":
    unittest.main()
