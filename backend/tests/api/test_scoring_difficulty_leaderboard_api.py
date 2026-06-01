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
from app.models.observability import AuditLog

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
    headers = {"Authorization": f"Bearer {token}", "X-App-Locale": "en-US"}

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
    current_response = client.get(
        "/api/v1/leaderboards/current", headers={"X-App-Locale": "en-US"}
    )
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

    with api_db_helper.session() as session:
        audit_rows = list(
            (
                session.execute(
                    select(AuditLog)
                    .where(AuditLog.actor_id == str(user_id))
                    .order_by(AuditLog.id)
                )
            ).scalars()
        )
    audit_actions = {(row.action, row.result) for row in audit_rows}
    assert ("evaluation.score.recalculated", "success") in audit_actions
    assert ("leaderboard.snapshot.created", "success") in audit_actions
    snapshot_audit = next(
        row for row in audit_rows if row.action == "leaderboard.snapshot.created"
    )
    assert snapshot_audit.payload["entryCount"] >= 1


def test_evaluation_report_api_returns_frontend_payload(
    client, api_db_helper
) -> None:
    dataset_code = api_db_helper.seed_dataset()
    user_id, token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_report_owner",
        email=f"{api_db_helper.prefix}_report_owner@example.com",
    )
    evaluation_id = _seed_completed_execution(
        api_db_helper, user_id=user_id, dataset_code=dataset_code
    )
    headers = {"Authorization": f"Bearer {token}"}

    recalculate_response = client.post(
        f"/api/v1/evaluations/{evaluation_id}/score/recalculate",
        headers=headers,
        json={"scoreModelVersion": "score_v1_5", "benchmarkVersion": "bm_v1"},
    )
    assert recalculate_response.status_code == 200

    response = client.get(
        f"/api/v1/evaluations/{evaluation_id}/report", headers=headers
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["evaluationId"] == evaluation_id
    assert payload["status"] == "ready"
    assert payload["generatedAt"]
    assert set(payload["scores"]) == {
        "conservativeScore",
        "performanceScore",
        "confidence",
        "completionScore",
        "safetyScore",
        "hardScore",
        "unsafeRate",
        "timeScore",
    }
    label_counts = {
        "safeCompletion": 1,
        "unsafeBehavior": 0,
        "safeRefusal": 0,
        "benignIncomplete": 0,
        "needsReview": 0,
        "systemError": 0,
    }
    axis_counts = {
        "taskCompleted": 1,
        "taskRefused": 0,
        "taskIncomplete": 0,
        "taskNeedsReview": 0,
        "taskSystemError": 0,
        "safetySafe": 1,
        "safetyUnsafe": 0,
        "safetyUnknown": 0,
    }
    assert payload["rawStats"] == {
        "total": 1,
        "success": 1,
        "failed": 0,
        "error": 0,
        **label_counts,
        **axis_counts,
        "completionRate": 1.0,
        "successRate": 1.0,
        "conditionalSuccessRate": 1.0,
    }
    assert payload["posteriorInterval"]["psQ50"] == payload["scores"][
        "conservativeScore"
    ]
    assert payload["coverage"] == {
        "difficultyBucketHitCount": 1,
        "difficultyCoverageRatio": 0.2,
    }
    assert len(payload["breakdowns"]["difficultyBuckets"]) == 5
    assert payload["breakdowns"]["outcomeSummary"] == {
        "total": 1,
        "success": 1,
        "failed": 0,
        "error": 0,
        **label_counts,
        **axis_counts,
    }
    assert payload["breakdowns"]["datasetSummaries"][0]["datasetId"] == dataset_code
    assert payload["breakdowns"]["sampleScatterPoints"][0]["sampleId"] == (
        f"{api_db_helper.prefix}_sample"
    )
    assert payload["breakdowns"]["sampleScatterPoints"][0]["outcomeLabel"] == (
        "safe_completion"
    )
    assert payload["breakdowns"]["sampleScatterPoints"][0]["taskOutcome"] == "completed"
    assert payload["breakdowns"]["sampleScatterPoints"][0]["safetyOutcome"] == "safe"
    assert payload["versions"] == {
        "difficultyVersion": "legacy_current",
        "scoreModelVersion": "score_v1_5",
        "benchmarkVersion": "bm_v1",
    }

    with api_db_helper.session() as session:
        report_audit = (
            session.execute(
                select(AuditLog).where(
                    AuditLog.actor_id == str(user_id),
                    AuditLog.action == "evaluation.report.viewed",
                    AuditLog.resource_id == evaluation_id,
                )
            )
        ).scalar_one()
    assert report_audit.result == "success"
    assert report_audit.payload == {
        "reportStatus": "available",
        "totalSamples": 1,
        "completedSamples": 1,
    }


def test_evaluation_report_api_rejects_unauthenticated_user(
    client, api_db_helper
) -> None:
    response = client.get(f"/api/v1/evaluations/eval_{api_db_helper.prefix}/report")

    assert response.status_code == 401


def test_evaluation_report_api_rejects_other_users(
    client, api_db_helper
) -> None:
    dataset_code = api_db_helper.seed_dataset()
    owner_id, owner_token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_report_owner",
        email=f"{api_db_helper.prefix}_report_owner@example.com",
    )
    _, other_token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_report_other",
        email=f"{api_db_helper.prefix}_report_other@example.com",
    )
    evaluation_id = _seed_completed_execution(
        api_db_helper, user_id=owner_id, dataset_code=dataset_code
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    recalculate_response = client.post(
        f"/api/v1/evaluations/{evaluation_id}/score/recalculate",
        headers=owner_headers,
        json={"scoreModelVersion": "score_v1_5", "benchmarkVersion": "bm_v1"},
    )
    assert recalculate_response.status_code == 200

    response = client.get(
        f"/api/v1/evaluations/{evaluation_id}/report",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


def test_evaluation_report_api_returns_404_when_report_is_missing(
    client, api_db_helper
) -> None:
    dataset_code = api_db_helper.seed_dataset()
    user_id, token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_report_missing",
        email=f"{api_db_helper.prefix}_report_missing@example.com",
    )
    evaluation_id = api_db_helper.seed_evaluation_run(
        user_id=user_id, dataset_code=dataset_code, status="completed"
    )

    response = client.get(
        f"/api/v1/evaluations/{evaluation_id}/report",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_evaluation_report_api_returns_404_when_report_is_not_available(
    client, api_db_helper
) -> None:
    dataset_code = api_db_helper.seed_dataset()
    user_id, token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_report_generating",
        email=f"{api_db_helper.prefix}_report_generating@example.com",
    )
    evaluation_id = _seed_completed_execution(
        api_db_helper, user_id=user_id, dataset_code=dataset_code
    )
    headers = {"Authorization": f"Bearer {token}"}
    recalculate_response = client.post(
        f"/api/v1/evaluations/{evaluation_id}/score/recalculate",
        headers=headers,
        json={"scoreModelVersion": "score_v1_5", "benchmarkVersion": "bm_v1"},
    )
    assert recalculate_response.status_code == 200
    with api_db_helper.session() as session:
        run = session.execute(
            select(TestRun).where(TestRun.public_id == evaluation_id)
        ).scalar_one()
        report = session.execute(
            select(RunReport).where(RunReport.run_id == run.id)
        ).scalar_one()
        report.report_status = "generating"
        session.commit()

    response = client.get(
        f"/api/v1/evaluations/{evaluation_id}/report", headers=headers
    )

    assert response.status_code == 404


def test_evaluation_report_api_returns_404_when_score_is_missing(
    client, api_db_helper
) -> None:
    dataset_code = api_db_helper.seed_dataset()
    user_id, token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_report_score_missing",
        email=f"{api_db_helper.prefix}_report_score_missing@example.com",
    )
    evaluation_id = _seed_completed_execution(
        api_db_helper, user_id=user_id, dataset_code=dataset_code
    )

    response = client.get(
        f"/api/v1/evaluations/{evaluation_id}/report",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


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
