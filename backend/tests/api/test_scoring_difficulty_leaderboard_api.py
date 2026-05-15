from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import (
    ExecutionSummary,
    RunReport,
    RunSample,
    SampleExecution,
    TestRun,
)

pytestmark = [pytest.mark.db, pytest.mark.integration]


def _seed_completed_execution(
    api_db_helper,
    *,
    user_id: int,
    dataset_code: str,
    public_to_leaderboard: bool = True,
    leaderboard_display_mode: str = "public",
) -> str:
    evaluation_id = api_db_helper.seed_evaluation_run(
        user_id=user_id, dataset_code=dataset_code, status="completed"
    )
    with api_db_helper.session() as session:
        run = session.execute(
            select(TestRun).where(TestRun.public_id == evaluation_id)
        ).scalar_one()
        run.public_to_leaderboard = public_to_leaderboard
        run.leaderboard_display_mode = leaderboard_display_mode
        run.completed_samples = 1
        run.success_count = 1
        run.failed_count = 0
        sample = session.execute(
            select(BenchmarkSample)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(RiskSubtype.code == dataset_code)
        ).scalar_one()
        run_sample = RunSample(
            run_id=run.id,
            sample_id_ref=sample.id,
            order_no=1,
            difficulty_version_code="legacy_current",
            difficulty_score_snapshot=Decimal("0.500"),
            completion_difficulty_snapshot=Decimal("0.500"),
            safety_difficulty_snapshot=Decimal("0.500"),
        )
        session.add(run_sample)
        session.flush()
        execution = SampleExecution(
            run_id=run.id,
            run_sample_id=run_sample.id,
            sample_id_ref=sample.id,
            status="done",
            retry_no=0,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        session.add(execution)
        session.flush()
        session.add(
            ExecutionSummary(
                sample_execution_id=execution.id,
                task_completed=True,
                harm_detected=False,
                summary_text="safe completion",
                final_label="safe",
            )
        )
        session.add(
            RunReport(
                run_id=run.id,
                report_status="available",
                summary_json={},
                report_uri=None,
            )
        )
        session.commit()
    return evaluation_id


def test_evaluation_score_and_leaderboard_api(client, api_db_helper) -> None:
    dataset_code = api_db_helper.seed_dataset()
    user_id, token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_score_owner",
        email=f"{api_db_helper.prefix}_score_owner@example.com",
    )
    evaluation_id = _seed_completed_execution(
        api_db_helper,
        user_id=user_id,
        dataset_code=dataset_code,
        leaderboard_display_mode="anonymous",
    )
    headers = {"Authorization": f"Bearer {token}"}

    recalculate_response = client.post(
        f"/api/v1/evaluations/{evaluation_id}/score/recalculate",
        headers=headers,
        json={"scoreModelVersion": "score_v1_5", "benchmarkVersion": "bm_v1"},
    )
    assert recalculate_response.status_code == 200
    score_payload = recalculate_response.json()["data"]
    assert score_payload["evaluationId"] == evaluation_id
    assert score_payload["officialConservativeScore"] is not None

    detail_response = client.get(
        f"/api/v1/evaluations/{evaluation_id}", headers=headers
    )
    assert detail_response.status_code == 200
    assert (
        detail_response.json()["data"]["score"]
        == score_payload["officialConservativeScore"]
    )

    unauthenticated_snapshot_response = client.post(
        "/api/v1/leaderboards/snapshots", json={}
    )
    assert unauthenticated_snapshot_response.status_code == 401

    snapshot_response = client.post(
        "/api/v1/leaderboards/snapshots", headers=headers, json={}
    )
    assert snapshot_response.status_code == 200
    current_response = client.get("/api/v1/leaderboards/current")
    assert current_response.status_code == 200
    entries = current_response.json()["data"]["entries"]
    assert entries
    assert any(
        entry["displayName"] == "Anonymous Agent" and entry["anonymous"] is True
        for entry in entries
    )
    assert all("agentId" not in entry for entry in entries)
    assert all("agentName" not in entry for entry in entries)
    assert all("evaluationId" not in entry for entry in entries)


def test_leaderboard_snapshot_keeps_legacy_private_runs_out(
    client, api_db_helper
) -> None:
    dataset_code = api_db_helper.seed_dataset()
    user_id, token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_private_owner",
        email=f"{api_db_helper.prefix}_private_owner@example.com",
    )
    evaluation_id = _seed_completed_execution(
        api_db_helper,
        user_id=user_id,
        dataset_code=dataset_code,
        public_to_leaderboard=False,
        leaderboard_display_mode="public",
    )
    headers = {"Authorization": f"Bearer {token}"}

    recalculate_response = client.post(
        f"/api/v1/evaluations/{evaluation_id}/score/recalculate",
        headers=headers,
        json={"scoreModelVersion": "score_v1_5", "benchmarkVersion": "bm_v1"},
    )
    assert recalculate_response.status_code == 200

    snapshot_response = client.post(
        "/api/v1/leaderboards/snapshots", headers=headers, json={}
    )
    assert snapshot_response.status_code == 200
    current_response = client.get("/api/v1/leaderboards/current")
    assert current_response.status_code == 200
    entries = current_response.json()["data"]["entries"]
    assert all(
        entry["displayName"] != f"{api_db_helper.prefix} agent" for entry in entries
    )


def test_difficulty_version_publish_updates_formal_sample_difficulty(
    client, api_db_helper
) -> None:
    dataset_code = api_db_helper.seed_dataset()
    user_id, token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_difficulty_owner",
        email=f"{api_db_helper.prefix}_difficulty_owner@example.com",
    )
    _seed_completed_execution(api_db_helper, user_id=user_id, dataset_code=dataset_code)
    headers = {"Authorization": f"Bearer {token}"}

    recalculate_response = client.post(
        "/api/v1/difficulty/versions/recalculate",
        headers=headers,
        json={
            "baseVersionCode": "legacy_current",
            "newVersionCode": f"{api_db_helper.prefix}_diff_v2",
        },
    )
    assert recalculate_response.status_code == 200

    publish_response = client.post(
        f"/api/v1/difficulty/versions/{api_db_helper.prefix}_diff_v2/publish",
        headers=headers,
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["data"]["publishedItemCount"] >= 1
