import importlib.util
import unittest


class WorkerRefactorBoundariesTestCase(unittest.TestCase):
    def test_worker_processing_module_exists(self) -> None:
        self.assertIsNotNone(importlib.util.find_spec("app.worker.processing"))

    def test_worker_execution_module_exists(self) -> None:
        self.assertIsNotNone(importlib.util.find_spec("app.worker.execution"))


if __name__ == "__main__":
    unittest.main()
