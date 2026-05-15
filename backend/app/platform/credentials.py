"""凭据存储能力，负责保存和读取敏感提交信息。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import uuid
from pathlib import Path
from typing import Protocol


class CredentialStore(Protocol):
    """定义凭据存储组件需要实现的接口。"""

    def store(self, payload: dict[str, object]) -> str:
        """保存凭据内容并返回可引用的外部标识。"""
        ...

    def load(self, credential_ref: str) -> dict[str, object]:
        """按引用标识读取原始凭据内容。"""
        ...

    def delete(self, credential_ref: str) -> None:
        """删除指定引用对应的凭据内容。"""
        ...


class FileCredentialStore:
    """基于本地文件的凭据存储实现。"""

    def __init__(self, base_dir: Path, secret_key: str) -> None:
        """初始化本地文件凭据仓库。"""
        self.base_dir = base_dir
        self.secret_key = secret_key.encode("utf-8")

    def store(self, payload: dict[str, object]) -> str:
        """将凭据写入本地文件并返回引用标识。"""
        credential_ref = f"secret_{uuid.uuid4().hex}"
        encoded = self._seal(payload)

        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / f"{credential_ref}.bin").write_text(encoded, encoding="utf-8")
        return credential_ref

    def load(self, credential_ref: str) -> dict[str, object]:
        """读取并解封指定引用的凭据内容。"""
        content = (self.base_dir / f"{credential_ref}.bin").read_text(encoding="utf-8")
        return self._open(content)

    def delete(self, credential_ref: str) -> None:
        """删除指定引用对应的本地凭据文件。"""
        path = self.base_dir / f"{credential_ref}.bin"
        if path.exists():
            path.unlink()

    def _seal(self, payload: dict[str, object]) -> str:
        """将凭据字典封装成可持久化的密文字符串。"""
        plaintext = json.dumps(
            payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        nonce = os.urandom(16)
        keystream = self._derive_keystream(nonce, len(plaintext))
        ciphertext = bytes(
            source ^ mask for source, mask in zip(plaintext, keystream, strict=True)
        )
        digest = hmac.new(self.secret_key, nonce + ciphertext, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(nonce + digest + ciphertext).decode("utf-8")

    def _open(self, sealed: str) -> dict[str, object]:
        """校验并解开持久化密文，恢复原始凭据字典。"""
        raw = base64.urlsafe_b64decode(sealed.encode("utf-8"))
        nonce = raw[:16]
        digest = raw[16:48]
        ciphertext = raw[48:]
        expected = hmac.new(
            self.secret_key, nonce + ciphertext, hashlib.sha256
        ).digest()
        if not hmac.compare_digest(digest, expected):
            raise ValueError("invalid secret payload")

        keystream = self._derive_keystream(nonce, len(ciphertext))
        plaintext = bytes(
            source ^ mask for source, mask in zip(ciphertext, keystream, strict=True)
        )
        return json.loads(plaintext.decode("utf-8"))

    def _derive_keystream(self, nonce: bytes, size: int) -> bytes:
        """按长度生成当前密文分段使用的伪随机密钥流。"""
        blocks: list[bytes] = []
        counter = 0
        while sum(len(block) for block in blocks) < size:
            block = hashlib.sha256(
                self.secret_key + nonce + counter.to_bytes(4, "big")
            ).digest()
            blocks.append(block)
            counter += 1
        return b"".join(blocks)[:size]
