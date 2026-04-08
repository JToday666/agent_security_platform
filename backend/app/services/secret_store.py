from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import uuid
from pathlib import Path


class LocalSecretStore:
    def __init__(self, base_dir: Path, secret_key: str) -> None:
        self.base_dir = base_dir
        self.secret_key = secret_key.encode("utf-8")

    def store(self, payload: dict[str, object]) -> str:
        credential_ref = f"secret_{uuid.uuid4().hex}"
        encoded = self._seal(payload)

        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / f"{credential_ref}.bin").write_text(encoded, encoding="utf-8")
        return credential_ref

    def load(self, credential_ref: str) -> dict[str, object]:
        content = (self.base_dir / f"{credential_ref}.bin").read_text(encoding="utf-8")
        return self._open(content)

    def _seal(self, payload: dict[str, object]) -> str:
        plaintext = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
        nonce = os.urandom(16)
        keystream = self._derive_keystream(nonce, len(plaintext))
        ciphertext = bytes(source ^ mask for source, mask in zip(plaintext, keystream, strict=True))
        digest = hmac.new(self.secret_key, nonce + ciphertext, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(nonce + digest + ciphertext).decode("utf-8")

    def _open(self, sealed: str) -> dict[str, object]:
        raw = base64.urlsafe_b64decode(sealed.encode("utf-8"))
        nonce = raw[:16]
        digest = raw[16:48]
        ciphertext = raw[48:]
        expected = hmac.new(self.secret_key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(digest, expected):
            raise ValueError("invalid secret payload")

        keystream = self._derive_keystream(nonce, len(ciphertext))
        plaintext = bytes(source ^ mask for source, mask in zip(ciphertext, keystream, strict=True))
        return json.loads(plaintext.decode("utf-8"))

    def _derive_keystream(self, nonce: bytes, size: int) -> bytes:
        blocks: list[bytes] = []
        counter = 0
        while sum(len(block) for block in blocks) < size:
            block = hashlib.sha256(self.secret_key + nonce + counter.to_bytes(4, "big")).digest()
            blocks.append(block)
            counter += 1
        return b"".join(blocks)[:size]
