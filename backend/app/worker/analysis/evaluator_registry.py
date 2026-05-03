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


class EvaluatorRegistry:
    """Runtime registry for oracle evaluator functions."""

    def __init__(self) -> None:
        self._evaluators: dict[str, EvaluatorFn] = {}

    def register(self, evaluator_type: str, evaluator: EvaluatorFn) -> None:
        """Register or replace an evaluator by its normalized type name."""
        normalized_type = self._normalize_type(evaluator_type)
        if not normalized_type:
            raise ValueError("evaluator_type must not be empty")
        self._evaluators[normalized_type] = evaluator

    def evaluate(self, oracle: OracleSpec, evidence: EvidenceBundle) -> OracleMatchResult:
        """Dispatch one oracle to its registered evaluator."""
        evaluator_type = self._normalize_type(oracle.evaluator_type) or "manual_review"
        normalized_oracle = replace(oracle, evaluator_type=evaluator_type)
        evaluator = self._evaluators.get(evaluator_type)
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

    def _normalize_type(self, evaluator_type: str) -> str:
        return evaluator_type.strip().lower()


def build_default_registry() -> EvaluatorRegistry:
    """Create a registry populated with built-in evaluator functions."""
    registry = EvaluatorRegistry()
    registry.register("event_trace_match", evaluate_event_trace_match)
    registry.register("completion_signal", evaluate_completion_signal)
    registry.register("manual_review", evaluate_review_required)
    registry.register("llm_judge", evaluate_llm_judge)
    return registry


DEFAULT_REGISTRY = build_default_registry()


def evaluate_oracle(oracle: OracleSpec, evidence: EvidenceBundle) -> OracleMatchResult:
    """Dispatch one oracle to its registered evaluator."""
    return DEFAULT_REGISTRY.evaluate(oracle, evidence)
