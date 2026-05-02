"""Registry for runtime oracle evaluator functions."""

from __future__ import annotations

from dataclasses import replace
from typing import Callable

from app.worker.analysis.evidence import EvidenceBundle
from app.worker.analysis.evaluator_types.completion import evaluate_completion_signal
from app.worker.analysis.evaluator_types.event_trace import evaluate_event_trace_match
from app.worker.analysis.evaluator_types.llm_judge import evaluate_llm_judge
from app.worker.analysis.evaluator_types.review import evaluate_review_required
from app.worker.analysis.schema import OracleMatchResult, OracleSpec


EvaluatorFn = Callable[[OracleSpec, EvidenceBundle], OracleMatchResult]


EVALUATORS: dict[str, EvaluatorFn] = {
    "event_trace_match": evaluate_event_trace_match,
    "completion_signal": evaluate_completion_signal,
    "manual_review": evaluate_review_required,
    "llm_judge": evaluate_llm_judge,
}


def evaluate_oracle(oracle: OracleSpec, evidence: EvidenceBundle) -> OracleMatchResult:
    """Dispatch one oracle to its registered evaluator."""
    evaluator_type = oracle.evaluator_type.strip().lower() or "manual_review"
    normalized_oracle = replace(oracle, evaluator_type=evaluator_type)
    evaluator = EVALUATORS.get(evaluator_type)
    if evaluator is None:
        return OracleMatchResult(
            oracle=normalized_oracle,
            matched=False,
            score=None,
            evidence_summary=f"unsupported evaluator_type: {evaluator_type}",
            evidence_ref={"evaluator_type": evaluator_type},
            needs_review=True,
        )
    return evaluator(normalized_oracle, evidence)
