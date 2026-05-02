"""Review-required evaluator placeholders."""

from __future__ import annotations

from app.worker.analysis.evidence import EvidenceBundle
from app.worker.analysis.schema import OracleMatchResult, OracleSpec


def evaluate_review_required(oracle: OracleSpec, evidence: EvidenceBundle) -> OracleMatchResult:
    """Mark semantic or manual evaluators as requiring review for now."""
    del evidence
    evaluator_type = oracle.evaluator_type.strip().lower() or "manual_review"
    return OracleMatchResult(
        oracle=oracle,
        matched=False,
        score=None,
        evidence_summary=f"{evaluator_type} requires review; automatic judging is disabled",
        evidence_ref={"evaluator_type": evaluator_type, "display_text": oracle.display_text},
        needs_review=True,
    )
