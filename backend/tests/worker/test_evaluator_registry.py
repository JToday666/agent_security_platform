from __future__ import annotations

from decimal import Decimal

import pytest

from app.worker.analysis.evidence import EvidenceBundle
from app.worker.analysis.evaluator_registry import EvaluatorRegistry, evaluate_oracle
from app.worker.analysis.schema import OracleMatchResult, OracleSpec

pytestmark = pytest.mark.worker


def _evidence(*, done: bool) -> EvidenceBundle:
    return EvidenceBundle(
        events=[],
        finalize_payload={"done": done},
        meta_payload={},
        evidence=[],
        warnings=[],
        errors=[],
    )


def _oracle(evaluator_type: str) -> OracleSpec:
    return OracleSpec(
        oracle_id=1,
        oracle_kind="success",
        oracle_kind_code=1,
        seq_no=1,
        display_text="registry test oracle",
        evaluator_type=evaluator_type,
        evaluator_config={},
    )


def test_registry_dispatches_registered_evaluator_and_marks_unsupported_for_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.worker.analysis.evaluator_types.llm_judge.settings.LLM_JUDGE_API_KEY", None
    )
    monkeypatch.setattr(
        "app.worker.analysis.evaluator_types.llm_judge.settings.LLM_JUDGE_PROVIDER",
        "deepseek",
    )

    completion_result = evaluate_oracle(
        _oracle(" completion_signal "), _evidence(done=True)
    )
    llm_result = evaluate_oracle(_oracle("llm_judge"), _evidence(done=False))
    unsupported_result = evaluate_oracle(
        _oracle("custom_checker"), _evidence(done=False)
    )

    assert completion_result.matched is True
    assert completion_result.score == Decimal("1.000")
    assert completion_result.needs_review is False

    assert llm_result.matched is False
    assert llm_result.score is None
    assert llm_result.needs_review is True
    assert llm_result.evidence_ref is not None
    assert llm_result.evidence_ref["status"] == "config_error"

    assert unsupported_result.matched is False
    assert unsupported_result.score is None
    assert unsupported_result.needs_review is True
    assert (
        unsupported_result.evidence_summary
        == "unsupported evaluator_type: custom_checker"
    )
    assert unsupported_result.evidence_ref == {"evaluator_type": "custom_checker"}


def test_custom_registry_can_register_runtime_evaluator() -> None:
    registry = EvaluatorRegistry()

    def custom_evaluator(oracle: OracleSpec, evidence: EvidenceBundle):
        return OracleMatchResult(
            oracle=oracle,
            matched=bool(evidence.finalize_payload.get("done")),
            score=Decimal("1.000"),
            evidence_summary="custom evaluator matched",
            evidence_ref={"source": "custom"},
            needs_review=False,
        )

    registry.register("custom_checker", custom_evaluator)
    result = registry.evaluate(_oracle(" custom_checker "), _evidence(done=True))

    assert result.matched is True
    assert result.needs_review is False
    assert result.oracle.evaluator_type == "custom_checker"
