import importlib
import importlib.util
import unittest


class AuthDependenciesTestCase(unittest.TestCase):
    def test_auth_dependency_module_exists(self) -> None:
        try:
            spec = importlib.util.find_spec("app.modules.auth.dependencies")
        except ModuleNotFoundError:
            spec = None
        self.assertIsNotNone(spec)

    def test_shared_auth_only_exports_db_dependency(self) -> None:
        module = importlib.import_module("app.shared.auth")
        self.assertTrue(hasattr(module, "get_db"))
        self.assertFalse(hasattr(module, "get_current_user"))


if __name__ == "__main__":
    unittest.main()
