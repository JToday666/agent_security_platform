"""密码与访问令牌相关的安全工具函数。"""

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from app.platform.config import settings


def hash_password(password: str) -> str:
    """生成带盐的密码摘要。"""
    salt = os.urandom(16)
    iterations = 100_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return (
        "pbkdf2_sha256"
        f"${iterations}"
        f"${base64.urlsafe_b64encode(salt).decode('utf-8')}"
        f"${base64.urlsafe_b64encode(digest).decode('utf-8')}"
    )


def verify_password(password: str, hashed_password: str) -> bool:
    """校验明文密码是否与摘要匹配。"""
    try:
        algorithm, iterations, salt_b64, hash_b64 = hashed_password.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
    expected_hash = base64.urlsafe_b64decode(hash_b64.encode("utf-8"))
    calculated_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, int(iterations)
    )
    return hmac.compare_digest(calculated_hash, expected_hash)


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """为指定用户生成访问令牌。"""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """解析访问令牌并返回载荷。"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
