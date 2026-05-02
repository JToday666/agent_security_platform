"""Compatibility wrapper for runtime analysis backed oracle evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from app.worker.analysis.schema import OracleMatchResult
from app.worker.analysis.service import ANALYSIS_VERSION, analyze_runtime_artifacts, summary_from_analysis


EVALUATOR_VERSION = ANALYSIS_VERSION


@dataclass(slots=True)
class OracleEvaluation:
    """单条 oracle 的运行时判定结果。"""

    oracle_id: int
    oracle_kind: int
    evaluator_type: str
    matched: bool
    score: Decimal | None
    evidence_summary: str | None
    evidence_ref: dict[str, object] | None
    needs_review: bool = False


@dataclass(slots=True)
class OracleEvaluationBundle:
    """一次样本执行的 oracle 明细与汇总。"""

    results: list[OracleEvaluation]
    summary: dict[str, object]


def evaluate_oracles_from_artifacts(
    oracles: Iterable[object],
    run_dir: Path,
    *,
    task_path: Path | None = None,
    output_path: Path | None = None,
) -> OracleEvaluationBundle:
    """Analyze runtime artifacts and return DB-compatible oracle results."""
    analysis_result = analyze_runtime_artifacts(
        run_dir=run_dir,
        task_path=task_path,
        oracles=oracles,
        output_path=output_path or (run_dir / "analysis_result.json"),
    )
    return OracleEvaluationBundle(
        results=[_to_oracle_evaluation(result) for result in analysis_result.oracle_results if result.oracle.oracle_id is not None],
        summary=summary_from_analysis(analysis_result),
    )


def _to_oracle_evaluation(result: OracleMatchResult) -> OracleEvaluation:
    oracle_id = result.oracle.oracle_id
    oracle_kind = result.oracle.oracle_kind_code
    if oracle_id is None or oracle_kind is None:
        raise ValueError("database oracle result requires oracle_id and oracle_kind")
    return OracleEvaluation(
        oracle_id=oracle_id,
        oracle_kind=oracle_kind,
        evaluator_type=result.oracle.evaluator_type,
        matched=result.matched,
        score=result.score,
        evidence_summary=result.evidence_summary,
        evidence_ref=result.evidence_ref,
        needs_review=result.needs_review,
    )
