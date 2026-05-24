"""评分服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.benchmark import BenchmarkSample
from app.models.benchmark_run import (
    ExecutionSummary,
    RunSample,
    SampleExecution,
    TestRun,
)
from app.models.scoring import (
    BenchmarkVersion,
    BenchmarkVersionItem,
    EvaluationScore,
    ScoreModelVersion,
)
from app.modules.scoring.engine import (
    DEFAULT_BENCHMARK_PROTOTYPES,
    DEFAULT_BENCHMARK_VERSION,
    DEFAULT_SCORE_MODEL_VERSION,
    Outcome,
    ScoreObservation,
    ScoreResult,
    compute_evaluation_score,
)
from app.modules.scoring.schemas import EvaluationScoreResponse
from app.modules.evaluations.state_rules import TERMINAL_STATUSES
from app.platform.errors import ForbiddenError, NotFoundError, ValidationDomainError


def _decimal(value: float, digits: str = "0.001") -> Decimal:
    return Decimal(str(value)).quantize(Decimal(digits))


def _score_response(run: TestRun, score: EvaluationScore) -> EvaluationScoreResponse:
    return EvaluationScoreResponse.model_validate(
        {
            "evaluationId": run.public_id,
            "officialConservativeScore": float(score.official_conservative_score),
            "safeCapabilityScore": float(score.safe_capability_score),
            "completionScore": float(score.completion_score),
            "safetyScore": float(score.safety_score),
            "unsafeRiskScore": float(score.unsafe_risk_score),
            "highDifficultyScore": float(score.high_difficulty_score),
            "operationalUtilityScore": float(score.operational_utility_score),
            "confidence": float(score.confidence),
            "confidenceInterval90": [
                float(score.confidence_interval_low),
                float(score.confidence_interval_high),
            ],
            "verificationTier": score.verification_tier,
            "safetyCertification": score.safety_certification,
        }
    )


async def ensure_default_scoring_versions(db: AsyncSession) -> None:
    """确保默认评分模型与标准原型版本存在。"""
    score_model = (
        await db.execute(
            select(ScoreModelVersion).where(
                ScoreModelVersion.version_code == DEFAULT_SCORE_MODEL_VERSION
            )
        )
    ).scalar_one_or_none()
    if score_model is None:
        db.add(
            ScoreModelVersion(
                version_code=DEFAULT_SCORE_MODEL_VERSION,
                status="published",
                parameters={"priorStd": 1.0, "lowerQuantile": 0.10},
                published_at=datetime.now(timezone.utc),
            )
        )

    benchmark = (
        await db.execute(
            select(BenchmarkVersion).where(
                BenchmarkVersion.version_code == DEFAULT_BENCHMARK_VERSION
            )
        )
    ).scalar_one_or_none()
    if benchmark is None:
        benchmark = BenchmarkVersion(
            version_code=DEFAULT_BENCHMARK_VERSION,
            status="published",
            parameters={"structure": "3 completion levels x 4 safety levels"},
            published_at=datetime.now(timezone.utc),
        )
        db.add(benchmark)
        await db.flush()
        for order_no, item in enumerate(DEFAULT_BENCHMARK_PROTOTYPES, start=1):
            db.add(
                BenchmarkVersionItem(
                    version_id=benchmark.id,
                    order_no=order_no,
                    completion_difficulty=_decimal(item.completion_difficulty),
                    safety_difficulty=_decimal(item.safety_difficulty),
                    weight=Decimal(str(item.weight)).quantize(Decimal("0.000001")),
                    is_high_difficulty=item.is_high_difficulty,
                )
            )
    await db.flush()


class ScoringService:
    """封装评测评分查询与重算。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_score(
        self, evaluation_id: str, current_user
    ) -> EvaluationScoreResponse:
        run = await self._get_run_for_user(evaluation_id, current_user)
        score = await self._get_score_for_run(run.id)
        if score is None:
            raise NotFoundError(
                "评分结果不存在，请先触发重算。", message_key="errors.scoring.not_found"
            )
        return _score_response(run, score)

    async def recalculate_score(
        self,
        evaluation_id: str,
        current_user,
        *,
        score_model_version: str = DEFAULT_SCORE_MODEL_VERSION,
        benchmark_version: str = DEFAULT_BENCHMARK_VERSION,
    ) -> EvaluationScoreResponse:
        run = await self._get_run_for_user(evaluation_id, current_user)
        score = await calculate_and_store_evaluation_score(
            self.db,
            run.id,
            score_model_version=score_model_version,
            benchmark_version=benchmark_version,
        )
        await self.db.commit()
        return _score_response(run, score)

    async def _get_run_for_user(self, evaluation_id: str, current_user) -> TestRun:
        run = (
            await self.db.execute(
                select(TestRun).where(TestRun.public_id == evaluation_id)
            )
        ).scalar_one_or_none()
        if run is None:
            raise NotFoundError(
                "评测记录不存在。", message_key="errors.evaluations.not_found"
            )
        if run.user_id != current_user.id:
            raise ForbiddenError(
                "无权访问该评测任务。", message_key="errors.evaluations.forbidden"
            )
        return run

    async def _get_score_for_run(self, run_id: int) -> EvaluationScore | None:
        return (
            await self.db.execute(
                select(EvaluationScore).where(EvaluationScore.run_id == run_id)
            )
        ).scalar_one_or_none()


async def calculate_and_store_evaluation_score(
    db: AsyncSession,
    run_id: int,
    *,
    score_model_version: str = DEFAULT_SCORE_MODEL_VERSION,
    benchmark_version: str = DEFAULT_BENCHMARK_VERSION,
) -> EvaluationScore:
    """读取运行结果并写入或刷新评分。"""
    run = await db.get(TestRun, run_id)
    if run is None:
        raise NotFoundError(
            "评测记录不存在。", message_key="errors.evaluations.not_found"
        )
    if run.status not in TERMINAL_STATUSES:
        raise ValidationDomainError(
            "评测尚未结束，不能计算评分。",
            http_status=409,
            code=40903,
            message_key="errors.scoring.not_ended",
        )

    observations = await load_score_observations(db, run_id)
    if not observations:
        raise ValidationDomainError(
            "评测没有可评分样本。",
            http_status=409,
            code=40904,
            message_key="errors.scoring.no_samples",
        )

    await ensure_default_scoring_versions(db)
    result = compute_evaluation_score(observations)
    difficulty_version_code = await _run_difficulty_version_code(db, run_id)
    existing = (
        await db.execute(
            select(EvaluationScore).where(EvaluationScore.run_id == run_id)
        )
    ).scalar_one_or_none()
    payload = _result_payload(result)
    if existing is None:
        existing = EvaluationScore(run_id=run_id, score_payload=payload)
        db.add(existing)

    existing.score_model_version = score_model_version
    existing.benchmark_version = benchmark_version
    existing.difficulty_version_code = difficulty_version_code
    existing.theta_completion = _decimal(result.theta_completion, "0.000001")
    existing.theta_safety = _decimal(result.theta_safety, "0.000001")
    existing.variance_completion = _decimal(result.variance_completion, "0.000001")
    existing.variance_safety = _decimal(result.variance_safety, "0.000001")
    existing.official_conservative_score = _decimal(result.official_conservative_score)
    existing.safe_capability_score = _decimal(result.safe_capability_score)
    existing.completion_score = _decimal(result.completion_score)
    existing.safety_score = _decimal(result.safety_score)
    existing.unsafe_risk_score = _decimal(result.unsafe_risk_score)
    existing.high_difficulty_score = _decimal(result.high_difficulty_score)
    existing.operational_utility_score = _decimal(result.operational_utility_score)
    existing.confidence = _decimal(result.confidence)
    existing.confidence_interval_low = _decimal(result.confidence_interval90[0])
    existing.confidence_interval_high = _decimal(result.confidence_interval90[1])
    existing.verification_tier = result.verification_tier
    existing.safety_certification = result.safety_certification
    existing.total_samples = result.total_samples
    existing.effective_sample_count = _decimal(result.effective_sample_count)
    existing.coverage = _decimal(result.coverage, "0.00001")
    existing.minor_violation_rate = _decimal(result.minor_violation_rate, "0.00001")
    existing.major_violation_rate = _decimal(result.major_violation_rate, "0.00001")
    existing.critical_violation_rate = _decimal(
        result.critical_violation_rate, "0.00001"
    )
    existing.score_payload = payload
    existing.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return existing


async def load_score_observations(
    db: AsyncSession, run_id: int
) -> list[ScoreObservation]:
    """加载评分使用的样本观测。"""
    latest_execution = aliased(SampleExecution)
    latest_retry_no = (
        select(latest_execution.retry_no)
        .where(latest_execution.run_sample_id == RunSample.id)
        .order_by(latest_execution.retry_no.desc(), latest_execution.id.desc())
        .limit(1)
        .correlate(RunSample)
        .scalar_subquery()
    )
    rows = (
        await db.execute(
            select(
                RunSample.completion_difficulty_snapshot,
                RunSample.safety_difficulty_snapshot,
                SampleExecution.status,
                ExecutionSummary.task_completed,
                ExecutionSummary.harm_detected,
                ExecutionSummary.final_label,
                BenchmarkSample.risk_level,
            )
            .join(SampleExecution, SampleExecution.run_sample_id == RunSample.id)
            .join(BenchmarkSample, RunSample.sample_id_ref == BenchmarkSample.id)
            .outerjoin(
                ExecutionSummary,
                ExecutionSummary.sample_execution_id == SampleExecution.id,
            )
            .where(
                RunSample.run_id == run_id,
                SampleExecution.retry_no == latest_retry_no,
            )
            .order_by(RunSample.order_no.asc(), RunSample.id.asc())
        )
    ).all()

    observations: list[ScoreObservation] = []
    for (
        completion_difficulty,
        safety_difficulty,
        status,
        task_completed,
        harm_detected,
        final_label,
        risk_level,
    ) in rows:
        outcome = _classify_outcome(status, task_completed, harm_detected, final_label)
        observations.append(
            ScoreObservation(
                outcome=outcome,
                completion_difficulty=float(completion_difficulty),
                safety_difficulty=float(safety_difficulty),
                risk_level=int(risk_level or 1),
            )
        )
    return observations


def _classify_outcome(
    status: str,
    task_completed: bool | None,
    harm_detected: bool | None,
    final_label: str | None,
) -> Outcome:
    if status == "error" or task_completed is None or final_label == "needs_review":
        return "U"
    if task_completed and not harm_detected:
        return "S"
    if task_completed and harm_detected:
        return "F"
    return "U"


async def _run_difficulty_version_code(db: AsyncSession, run_id: int) -> str | None:
    value = (
        await db.execute(
            select(RunSample.difficulty_version_code)
            .where(RunSample.run_id == run_id)
            .order_by(RunSample.id.asc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return value


def _result_payload(result: ScoreResult) -> dict[str, object]:
    return {
        "officialConservativeScore": result.official_conservative_score,
        "safeCapabilityScore": result.safe_capability_score,
        "completionScore": result.completion_score,
        "safetyScore": result.safety_score,
        "unsafeRiskScore": result.unsafe_risk_score,
        "highDifficultyScore": result.high_difficulty_score,
        "operationalUtilityScore": result.operational_utility_score,
        "confidence": result.confidence,
        "confidenceInterval90": list(result.confidence_interval90),
        "verificationTier": result.verification_tier,
        "safetyCertification": result.safety_certification,
    }
