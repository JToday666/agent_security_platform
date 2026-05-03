"""Structured runtime analysis schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


JsonObject = dict[str, Any]


def json_safe(value: Any) -> Any:
    """Convert internal values into JSON-serializable data."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    return value


@dataclass(slots=True)
class EvidenceItem:
    """A compact, structured reference to runtime evidence."""

    source: str
    summary: str
    index: int | None = None
    event_type: str | None = None
    target: JsonObject | None = None
    value: Any = None

    def to_dict(self) -> JsonObject:
        payload: JsonObject = {
            "source": self.source,
            "summary": self.summary,
        }
        if self.index is not None:
            payload["index"] = self.index
        if self.event_type:
            payload["event_type"] = self.event_type
        if self.target:
            payload["target"] = json_safe(self.target)
        if self.value is not None:
            payload["value"] = json_safe(self.value)
        return payload


@dataclass(slots=True)
class OracleSpec:
    """Normalized oracle metadata from task.json or database rows."""

    oracle_id: int | None
    oracle_kind: str
    oracle_kind_code: int | None
    seq_no: int
    display_text: str
    evaluator_type: str
    evaluator_config: JsonObject


@dataclass(slots=True)
class OracleMatchResult:
    """Result for one oracle evaluation."""

    oracle: OracleSpec
    matched: bool
    score: Decimal | None
    evidence_summary: str | None
    evidence_ref: JsonObject | None
    needs_review: bool = False

    def to_public_dict(self) -> JsonObject:
        payload: JsonObject = {
            "oracle_id": self.oracle.oracle_id,
            "kind": self.oracle.oracle_kind,
            "seq_no": self.oracle.seq_no,
            "display_text": self.oracle.display_text,
            "evaluator_type": self.oracle.evaluator_type,
            "matched": self.matched,
            "score": json_safe(self.score),
            "needs_review": self.needs_review,
            "evidence_summary": self.evidence_summary,
            "evidence_ref": json_safe(self.evidence_ref or {}),
        }
        return payload


@dataclass(slots=True)
class AnalysisResult:
    """Top-level analysis result written to analysis_result.json."""

    task_completed: bool
    safe: bool
    harm_detected: bool
    needs_review: bool
    confidence: str
    completion_reason: str
    safety_reason: str
    matched_success_oracles: list[JsonObject]
    matched_harm_oracles: list[JsonObject]
    evidence: list[JsonObject]
    warnings: list[str]
    errors: list[str]
    oracle_results: list[OracleMatchResult] = field(default_factory=list, repr=False)

    def to_dict(self) -> JsonObject:
        return {
            "task_completed": self.task_completed,
            "safe": self.safe,
            "harm_detected": self.harm_detected,
            "needs_review": self.needs_review,
            "confidence": self.confidence,
            "completion_reason": self.completion_reason,
            "safety_reason": self.safety_reason,
            "matched_success_oracles": json_safe(self.matched_success_oracles),
            "matched_harm_oracles": json_safe(self.matched_harm_oracles),
            "evidence": json_safe(self.evidence),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }
