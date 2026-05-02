"""Completion-signal evaluator."""

from __future__ import annotations

from decimal import Decimal

from app.worker.analysis.evidence import EvidenceBundle
from app.worker.analysis.schema import OracleMatchResult, OracleSpec


def evaluate_completion_signal(oracle: OracleSpec, evidence: EvidenceBundle) -> OracleMatchResult:
    """Evaluate completion from runtime finalize payload."""
    matched = bool(evidence.finalize_payload.get("done"))
    return OracleMatchResult(
        oracle=oracle,
        matched=matched,
        score=Decimal("1.000") if matched else Decimal("0.000"),
        evidence_summary="runtime finalize reported done=true" if matched else "runtime finalize did not report done=true",
        evidence_ref={"artifact": "finalize.json", "done": evidence.finalize_payload.get("done")},
        needs_review=False,
    )
