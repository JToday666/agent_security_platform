from __future__ import annotations

from pathlib import Path

from app.platform.credentials import FileCredentialStore


def test_store_roundtrip_uses_reference_not_plaintext(tmp_path: Path) -> None:
    store = FileCredentialStore(base_dir=tmp_path, secret_key="unit-test-secret")

    credential_ref = store.store(
        {
            "submitMethod": "api",
            "token": "sk-secret-token",
            "baseUrl": "https://example.com/agent/run",
        }
    )
    restored = store.load(credential_ref)
    content = (tmp_path / f"{credential_ref}.bin").read_text(encoding="utf-8")

    assert restored["token"] == "sk-secret-token"
    assert "sk-secret-token" not in content
    assert credential_ref.startswith("secret_")
