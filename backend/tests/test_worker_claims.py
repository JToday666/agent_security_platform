from datetime import datetime, timedelta, timezone
import importlib
import importlib.util
import unittest


class WorkerClaimRulesTestCase(unittest.TestCase):
    def test_worker_claim_module_exists_and_marks_stale_claims(self) -> None:
        try:
            spec = importlib.util.find_spec("app.worker.claims")
        except ModuleNotFoundError:
            spec = None
        self.assertIsNotNone(spec)

        claims = importlib.import_module("app.worker.claims")
        stale_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        fresh_at = datetime.now(timezone.utc) - timedelta(seconds=10)

        self.assertTrue(claims.claim_is_stale(stale_at, stale_after_seconds=30))
        self.assertFalse(claims.claim_is_stale(fresh_at, stale_after_seconds=30))
        self.assertFalse(claims.claim_is_stale(None, stale_after_seconds=30))


if __name__ == "__main__":
    unittest.main()
