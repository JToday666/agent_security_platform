from pathlib import Path
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class ArchitectureCleanupTestCase(unittest.TestCase):
    def test_no_legacy_backend_import_paths_remain(self) -> None:
        target_files = [
            *BACKEND_ROOT.joinpath("app").rglob("*.py"),
            BACKEND_ROOT / "run.py",
            BACKEND_ROOT / "alembic" / "env.py",
        ]
        forbidden_patterns = [
            ".".join(["app", "api", "v1", "endpoints"]),
            ".".join(["app", "services"]),
            ".".join(["app", "crud"]),
            ".".join(["app", "core"]),
            ".".join(["app", "db"]),
            ".".join(["app", "api", "response"]),
            ".".join(["app", "api", "deps"]),
            ".".join(["app", "schemas"]),
        ]

        violations: list[str] = []
        for path in target_files:
            source = path.read_text(encoding="utf-8")
            for pattern in forbidden_patterns:
                if pattern in source:
                    violations.append(f"{path.relative_to(BACKEND_ROOT)} -> {pattern}")

        self.assertEqual([], violations)

    def test_legacy_compatibility_files_are_removed(self) -> None:
        legacy_paths = [
            "app/api/v1/endpoints/auth.py",
            "app/api/v1/endpoints/user.py",
            "app/api/v1/endpoints/datasets.py",
            "app/api/v1/endpoints/agents.py",
            "app/api/v1/endpoints/evaluations.py",
            "app/services/__init__.py",
            "app/services/datasets.py",
            "app/services/evaluations.py",
            "app/services/runtime_rules.py",
            "app/services/secret_store.py",
            "app/services/simulator.py",
            "app/services/submissions.py",
            "app/crud/__init__.py",
            "app/crud/user.py",
            "app/core/config.py",
            "app/core/security.py",
            "app/db/base.py",
            "app/db/session.py",
            "app/schemas/__init__.py",
            "app/schemas/agents.py",
            "app/schemas/auth.py",
            "app/schemas/base.py",
            "app/schemas/datasets.py",
            "app/schemas/evaluations.py",
            "app/schemas/user.py",
            "app/api/deps.py",
            "app/api/response.py",
        ]

        remaining = [path for path in legacy_paths if (BACKEND_ROOT / path).exists()]
        self.assertEqual([], remaining)


if __name__ == "__main__":
    unittest.main()
