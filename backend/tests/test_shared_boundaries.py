import importlib
import importlib.util
import unittest


class SharedBoundariesTestCase(unittest.TestCase):
    def test_shared_runtime_rules_only_exports_submission_helpers(self) -> None:
        module = importlib.import_module("app.shared.runtime_rules")
        self.assertTrue(hasattr(module, "difficulty_bucket_bounds"))
        self.assertTrue(hasattr(module, "is_valid_request_id"))
        self.assertFalse(hasattr(module, "build_controls"))
        self.assertFalse(hasattr(module, "apply_pause_timeout"))
        self.assertFalse(hasattr(module, "TERMINAL_STATUSES"))

    def test_shared_run_lifecycle_module_is_removed(self) -> None:
        self.assertIsNone(importlib.util.find_spec("app.shared.run_lifecycle"))


if __name__ == "__main__":
    unittest.main()
