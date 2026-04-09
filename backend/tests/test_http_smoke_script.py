from pathlib import Path
import importlib.util
import subprocess
import sys
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class HttpSmokeScriptTestCase(unittest.TestCase):
    def test_http_smoke_script_exists_and_supports_help(self) -> None:
        script_path = BACKEND_ROOT / "scripts" / "http_smoke_check.py"
        self.assertTrue(script_path.exists())

        spec = importlib.util.spec_from_file_location("http_smoke_check", script_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=BACKEND_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Run live HTTP smoke checks", result.stdout)


if __name__ == "__main__":
    unittest.main()
