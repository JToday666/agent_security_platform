"""动态难度服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark import BenchmarkSample
from app.models.benchmark_run import ExecutionSummary, RunSample, SampleDifficultyStat, SampleExecution
from app.models.scoring import DifficultyVersion, DifficultyVersionItem
from app.modules.difficulty.calibration import (
    DEFAULT_MAX_DELTA_PER_VERSION,
    DEFAULT_PRIOR_STRENGTH,
    DEFAULT_PUBLISH_TAU,
    DifficultyStatsSnapshot,
    calculate_candidate_difficulty,
    publish_difficulty_value,
)
from app.modules.difficulty.schemas import DifficultyPublishResult, DifficultyVersionResult
from app.platform.errors import ConflictError, NotFoundError


def _decimal(value: float, digits: str = "0.001") -> Decimal:
    return Decimal(str(value)).quantize(Decimal(digits))


class DifficultyService:
    """封装难度版本重算与发布。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def recalculate_version(
        self,
        *,
        base_version_code: str,
        new_version_code: str,
        stats_cutoff_at: str | None = None,
    ) -> DifficultyVersionResult:
        existing = (
            await self.db.execute(select(DifficultyVersion).where(DifficultyVersion.version_code == new_version_code))
        ).scalar_one_or_none()
        if existing is not None:
            raise ConflictError("难度版本编号已存在。", code=40910)

        cutoff = _parse_zulu(stats_cutoff_at)
        version = DifficultyVersion(
            version_code=new_version_code,
            status="draft",
            base_version_code=base_version_code,
            stats_cutoff_at=cutoff,
            parameters={
                "priorStrength": DEFAULT_PRIOR_STRENGTH,
                "publishTau": DEFAULT_PUBLISH_TAU,
                "maxDeltaPerVersion": DEFAULT_MAX_DELTA_PER_VERSION,
            },
        )
        self.db.add(version)
        await self.db.flush()

        sample_rows = list(
            (
                await self.db.execute(
                    select(BenchmarkSample, SampleDifficultyStat)
                    .outerjoin(SampleDifficultyStat, SampleDifficultyStat.sample_id_ref == BenchmarkSample.id)
                    .where(BenchmarkSample.is_active.is_(True))
                    .order_by(BenchmarkSample.id.asc())
                )
            ).all()
        )
        base_items = await self._load_base_items(base_version_code)
        for sample, stats in sample_rows:
            base = base_items.get(sample.id)
            base_score = float(base.difficulty_score) if base is not None else float(sample.difficulty_score)
            base_completion = float(base.completion_difficulty) if base is not None else base_score
            base_safety = float(base.safety_difficulty) if base is not None else base_score
            candidate = _candidate_from_stats(sample, stats)
            completion = publish_difficulty_value(
                base_value=base_completion,
                candidate_value=candidate.completion_difficulty,
            )
            safety = publish_difficulty_value(
                base_value=base_safety,
                candidate_value=candidate.safety_difficulty,
            )
            combined_candidate = candidate.difficulty_score
            combined = publish_difficulty_value(base_value=base_score, candidate_value=combined_candidate)
            self.db.add(
                DifficultyVersionItem(
                    version_id=version.id,
                    sample_id_ref=sample.id,
                    previous_difficulty_score=_decimal(base_score),
                    candidate_completion_difficulty=_decimal(candidate.completion_difficulty),
                    candidate_safety_difficulty=_decimal(candidate.safety_difficulty),
                    candidate_difficulty_score=_decimal(combined_candidate),
                    completion_difficulty=_decimal(completion),
                    safety_difficulty=_decimal(safety),
                    difficulty_score=_decimal(combined),
                    valid_execution_count=0 if stats is None else stats.valid_execution_count,
                )
            )
        version.item_count = len(sample_rows)
        await self.db.commit()
        return DifficultyVersionResult(version_code=version.version_code, status=version.status, item_count=version.item_count)

    async def publish_version(self, version_code: str) -> DifficultyPublishResult:
        version = (
            await self.db.execute(select(DifficultyVersion).where(DifficultyVersion.version_code == version_code))
        ).scalar_one_or_none()
        if version is None:
            raise NotFoundError("难度版本不存在。")

        items = list(
            (
                await self.db.execute(
                    select(DifficultyVersionItem).where(DifficultyVersionItem.version_id == version.id)
                )
            ).scalars()
        )
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(DifficultyVersion)
            .where(DifficultyVersion.status == "published", DifficultyVersion.id != version.id)
            .values(status="archived")
        )
        for item in items:
            await self.db.execute(
                update(BenchmarkSample)
                .where(BenchmarkSample.id == item.sample_id_ref)
                .values(difficulty_score=item.difficulty_score, difficulty_updated_at=now)
            )
        version.status = "published"
        version.published_at = now
        version.item_count = len(items)
        await self.db.commit()
        return DifficultyPublishResult(
            version_code=version.version_code,
            status=version.status,
            published_item_count=len(items),
        )

    async def _load_base_items(self, base_version_code: str) -> dict[int, DifficultyVersionItem]:
        if base_version_code == "legacy_current":
            return {}
        version = (
            await self.db.execute(select(DifficultyVersion).where(DifficultyVersion.version_code == base_version_code))
        ).scalar_one_or_none()
        if version is None:
            return {}
        rows = list(
            (
                await self.db.execute(
                    select(DifficultyVersionItem).where(DifficultyVersionItem.version_id == version.id)
                )
            ).scalars()
        )
        return {row.sample_id_ref: row for row in rows}


async def update_sample_difficulty_stats_for_run(db: AsyncSession, run_id: int) -> None:
    """根据一次评测结果刷新样本难度统计缓存。"""
    rows = (
        await db.execute(
            select(
                RunSample.sample_id_ref,
                SampleExecution.status,
                ExecutionSummary.task_completed,
                ExecutionSummary.harm_detected,
                ExecutionSummary.final_label,
                BenchmarkSample.risk_level,
                BenchmarkSample.difficulty_seed,
            )
            .join(SampleExecution, SampleExecution.run_sample_id == RunSample.id)
            .join(BenchmarkSample, RunSample.sample_id_ref == BenchmarkSample.id)
            .outerjoin(ExecutionSummary, ExecutionSummary.sample_execution_id == SampleExecution.id)
            .where(RunSample.run_id == run_id, SampleExecution.retry_no == 0)
        )
    ).all()

    now = datetime.now(timezone.utc)
    for sample_id, status, task_completed, harm_detected, final_label, risk_level, seed in rows:
        stat = await db.get(SampleDifficultyStat, sample_id)
        if stat is None:
            stat = SampleDifficultyStat(
                sample_id_ref=sample_id,
                valid_execution_count=0,
                completed_count=0,
                unfinished_count=0,
                harm_count=0,
                safe_completion_count=0,
                minor_harm_count=0,
                major_harm_count=0,
                critical_harm_count=0,
                harm_rate=Decimal("0.0000"),
                safe_completion_rate=Decimal("0.0000"),
                inferred_difficulty=Decimal(seed),
                candidate_completion_difficulty=Decimal(seed),
                candidate_safety_difficulty=Decimal(seed),
                candidate_difficulty_score=Decimal(seed),
                algorithm_version="difficulty_calibration_v1",
                last_execution_at=now,
                updated_at=now,
            )
            db.add(stat)

        stat.valid_execution_count += 1
        outcome = _difficulty_outcome(status, task_completed, harm_detected, final_label)
        if outcome == "unfinished":
            stat.unfinished_count += 1
        else:
            stat.completed_count += 1
            if outcome == "safe":
                stat.safe_completion_count += 1
            else:
                stat.harm_count += 1
                if int(risk_level or 1) >= 3:
                    stat.critical_harm_count += 1
                elif int(risk_level or 1) == 2:
                    stat.major_harm_count += 1
                else:
                    stat.minor_harm_count += 1

        candidate = calculate_candidate_difficulty(
            DifficultyStatsSnapshot(
                seed_difficulty=float(seed),
                valid_execution_count=stat.valid_execution_count,
                completed_count=stat.completed_count,
                safe_completion_count=stat.safe_completion_count,
                harm_count=stat.harm_count,
            )
        )
        stat.harm_rate = _decimal(stat.harm_count / max(1, stat.valid_execution_count), "0.0001")
        stat.safe_completion_rate = _decimal(stat.safe_completion_count / max(1, stat.completed_count), "0.0001")
        stat.inferred_difficulty = _decimal(candidate.difficulty_score)
        stat.candidate_completion_difficulty = _decimal(candidate.completion_difficulty)
        stat.candidate_safety_difficulty = _decimal(candidate.safety_difficulty)
        stat.candidate_difficulty_score = _decimal(candidate.difficulty_score)
        stat.algorithm_version = "difficulty_calibration_v1"
        stat.last_execution_at = now
        stat.updated_at = now
    await db.flush()


def _candidate_from_stats(sample: BenchmarkSample, stats: SampleDifficultyStat | None):
    if stats is None:
        return calculate_candidate_difficulty(
            DifficultyStatsSnapshot(
                seed_difficulty=float(sample.difficulty_seed),
                valid_execution_count=0,
                completed_count=0,
                safe_completion_count=0,
                harm_count=0,
            )
        )
    return calculate_candidate_difficulty(
        DifficultyStatsSnapshot(
            seed_difficulty=float(sample.difficulty_seed),
            valid_execution_count=stats.valid_execution_count,
            completed_count=stats.completed_count,
            safe_completion_count=stats.safe_completion_count,
            harm_count=stats.harm_count,
        )
    )


def _difficulty_outcome(status: str, task_completed: bool | None, harm_detected: bool | None, final_label: str | None) -> str:
    if status == "error" or task_completed is None or final_label == "needs_review":
        return "unfinished"
    if task_completed and harm_detected:
        return "harm"
    if task_completed and not harm_detected:
        return "safe"
    return "unfinished"


def _parse_zulu(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)
