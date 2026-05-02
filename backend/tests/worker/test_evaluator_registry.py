from __future__ import annotations

from decimal import Decimal

import pytest

from app.worker.analysis.evidence import EvidenceBundle
from app.worker.analysis.evaluator_registry import evaluate_oracle
from app.worker.analysis.schema import OracleSpec


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


def test_registry_dispatches_registered_evaluator_and_marks_unsupported_for_review() -> None:
    completion_result = evaluate_oracle(_oracle(" completion_signal "), _evidence(done=True))
    unsupported_result = evaluate_oracle(_oracle("custom_checker"), _evidence(done=False))

    assert completion_result.matched is True
    assert completion_result.score == Decimal("1.000")
    assert completion_result.needs_review is False

    assert unsupported_result.matched is False
    assert unsupported_result.score is None
    assert unsupported_result.needs_review is True
    assert unsupported_result.evidence_summary == "unsupported evaluator_type: custom_checker"
    assert unsupported_result.evidence_ref == {"evaluator_type": "custom_checker"}
