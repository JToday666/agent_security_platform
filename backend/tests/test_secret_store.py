import tempfile
import unittest
from pathlib import Path

from app.shared.credentials import FileCredentialStore


class LocalSecretStoreTestCase(unittest.TestCase):
    def test_store_roundtrip_uses_reference_not_plaintext(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileCredentialStore(base_dir=Path(tmpdir), secret_key="unit-test-secret")

            credential_ref = store.store(
                {
                    "submitMethod": "api",
                    "token": "sk-secret-token",
                    "baseUrl": "https://example.com/agent/run",
                }
            )
            restored = store.load(credential_ref)
            content = (Path(tmpdir) / f"{credential_ref}.bin").read_text(encoding="utf-8")

            self.assertEqual(restored["token"], "sk-secret-token")
            self.assertNotIn("sk-secret-token", content)
            self.assertTrue(credential_ref.startswith("secret_"))


if __name__ == "__main__":
    unittest.main()
