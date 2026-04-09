import unittest
from datetime import datetime, timedelta, timezone

from app.modules.evaluations.state_rules import (
    TERMINAL_STATUSES,
    apply_pause_timeout,
    build_controls,
)


class EvaluationStateRulesTestCase(unittest.TestCase):
    def test_terminal_statuses_are_defined_for_run_domain(self) -> None:
        self.assertEqual({"completed", "terminated", "canceled", "failed"}, TERMINAL_STATUSES)

    def test_build_controls_for_running_and_paused_states(self) -> None:
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
