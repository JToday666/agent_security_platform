"""排行榜服务。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark_run import TestRun
from app.models.scoring import EvaluationScore, LeaderboardEntry, LeaderboardSnapshot
from app.modules.leaderboards.schemas import (
    LeaderboardEntryItem,
    LeaderboardSnapshotResponse,
)
from app.platform.errors import NotFoundError
from app.platform.i18n import translate


class LeaderboardService:
    """生成与查询排行榜快照。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_snapshot(
        self, *, score_model_version: str, benchmark_version: str
    ) -> LeaderboardSnapshotResponse:
        rows = (
            await self.db.execute(
                select(EvaluationScore, TestRun)
                .join(TestRun, EvaluationScore.run_id == TestRun.id)
                .where(
                    TestRun.public_to_leaderboard.is_(True),
                    EvaluationScore.score_model_version == score_model_version,
                    EvaluationScore.benchmark_version == benchmark_version,
                )
            )
        ).all()
        ranked_rows = _best_score_per_agent([(score, run) for score, run in rows])
        snapshot = LeaderboardSnapshot(
            snapshot_code=f"lb_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            status="published",
            score_model_version=score_model_version,
            benchmark_version=benchmark_version,
            difficulty_version_code=(
                ranked_rows[0][0].difficulty_version_code if ranked_rows else None
            ),
            generated_at=datetime.now(timezone.utc),
            entry_count=len(ranked_rows),
        )
        await self.db.execute(
            update(LeaderboardSnapshot)
            .where(LeaderboardSnapshot.status == "published")
            .values(status="archived")
        )
        self.db.add(snapshot)
        await self.db.flush()
        entries: list[LeaderboardEntry] = []
        for rank_no, (score, run) in enumerate(ranked_rows, start=1):
            agent_id = _agent_id(run)
            anonymous = run.leaderboard_display_mode == "anonymous"
            entry = LeaderboardEntry(
                snapshot_id=snapshot.id,
                score_id=score.id,
                run_id=run.id,
                rank_no=rank_no,
                agent_id=agent_id,
                agent_name=run.agent_name,
                evaluation_id=run.public_id,
                display_name="Anonymous Agent" if anonymous else run.agent_name,
                anonymous=anonymous,
                official_conservative_score=score.official_conservative_score,
                safe_capability_score=score.safe_capability_score,
                high_difficulty_score=score.high_difficulty_score,
                unsafe_risk_score=score.unsafe_risk_score,
                confidence=score.confidence,
                verification_tier=score.verification_tier,
                safety_certification=score.safety_certification,
                total_samples=score.total_samples,
            )
            self.db.add(entry)
            entries.append(entry)
        await self.db.commit()
        return _snapshot_response(snapshot, entries)

    async def get_current_snapshot(self) -> LeaderboardSnapshotResponse:
        snapshot = (
            await self.db.execute(
                select(LeaderboardSnapshot)
                .where(LeaderboardSnapshot.status == "published")
                .order_by(
                    LeaderboardSnapshot.generated_at.desc(),
                    LeaderboardSnapshot.id.desc(),
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if snapshot is None:
            raise NotFoundError(
                "当前排行榜不存在。", message_key="errors.leaderboard.not_found"
            )
        entries = list(
            (
                await self.db.execute(
                    select(LeaderboardEntry)
                    .where(LeaderboardEntry.snapshot_id == snapshot.id)
                    .order_by(LeaderboardEntry.rank_no.asc())
                )
            ).scalars()
        )
        return _snapshot_response(snapshot, entries)


def _best_score_per_agent(
    rows: list[tuple[EvaluationScore, TestRun]],
) -> list[tuple[EvaluationScore, TestRun]]:
    sorted_rows = sorted(rows, key=_ranking_key)
    selected: dict[str, tuple[EvaluationScore, TestRun]] = {}
    for score, run in sorted_rows:
        selected.setdefault(_agent_id(run), (score, run))
    return list(selected.values())


def _ranking_key(row: tuple[EvaluationScore, TestRun]) -> tuple:
    score, run = row
    certification_rank = {"certified": 0, "watchlist": 1, "blocked": 2}.get(
        score.safety_certification, 3
    )
    tier_rank = {"verified": 0, "provisional": 1, "exploratory": 2}.get(
        score.verification_tier, 3
    )
    return (
        certification_rank,
        tier_rank,
        -float(score.official_conservative_score),
        -float(score.safe_capability_score),
        -float(score.high_difficulty_score),
        float(score.unsafe_risk_score),
        -float(score.confidence),
        _agent_id(run),
    )


def _agent_id(run: TestRun) -> str:
    if isinstance(run.execution_config, dict):
        value = run.execution_config.get("agentId")
        if value:
            return str(value)
    return f"run:{run.public_id}"


def _snapshot_response(
    snapshot: LeaderboardSnapshot, entries: list[LeaderboardEntry]
) -> LeaderboardSnapshotResponse:
    return LeaderboardSnapshotResponse.model_validate(
        {
            "snapshotCode": snapshot.snapshot_code,
            "entryCount": len(entries),
            "entries": [
                {
                    "rankNo": entry.rank_no,
                    "displayName": (
                        translate("leaderboard.anonymous_agent")
                        if entry.anonymous
                        else entry.display_name
                    ),
                    "anonymous": entry.anonymous,
                    "officialConservativeScore": float(
                        entry.official_conservative_score
                    ),
                    "safeCapabilityScore": float(entry.safe_capability_score),
                    "highDifficultyScore": float(entry.high_difficulty_score),
                    "unsafeRiskScore": float(entry.unsafe_risk_score),
                    "confidence": float(entry.confidence),
                    "verificationTier": entry.verification_tier,
                    "safetyCertification": entry.safety_certification,
                    "totalSamples": entry.total_samples,
                }
                for entry in entries
            ],
        }
    )
