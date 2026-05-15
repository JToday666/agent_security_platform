"""Evaluation public identifier and idempotency helpers."""

import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from app.modules.evaluations.schemas import EvaluationCreateRequest


def generate_public_id() -> str:
    """Generate a public evaluation run identifier."""
    return (
        f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
    )


def request_fingerprint(payload: EvaluationCreateRequest) -> str:
    """Build a stable request body hash for requestId idempotency."""
    encoded = json.dumps(
        payload.model_dump(by_alias=True),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
