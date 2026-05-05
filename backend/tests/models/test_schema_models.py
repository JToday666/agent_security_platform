from __future__ import annotations

from app.models.benchmark import RiskCategory, RiskSubtype, RiskSubtypeDisplayMeta, SampleOracle
from app.models.benchmark_run import RunDataset, SampleExecution, TestRun as EvaluationRunModel
from app.models.scoring import LeaderboardEntry


def test_risk_category_has_display_columns() -> None:
    assert "meaning" in RiskCategory.__table__.c
    assert "updated_at" in RiskCategory.__table__.c


def test_risk_subtype_display_meta_exists() -> None:
    columns = RiskSubtypeDisplayMeta.__table__.c
    assert "subtype_id" in columns
    assert "short_description" in columns
    assert "full_description" in columns
    assert "highlights" in columns
    assert "scenarios" in columns
    assert "resources" in columns
    assert "media" in columns
    assert "updated_at" in columns


def test_test_run_has_public_interface_columns() -> None:
    columns = EvaluationRunModel.__table__.c
    assert "public_id" in columns
    assert "agent_name" in columns
    assert "description" in columns
    assert "submit_method" in columns
    assert "public_to_leaderboard" in columns
    assert "leaderboard_display_mode" in columns
    assert "request_id" in columns
    assert "updated_at" in columns
    assert "finalization_reason" in columns
    assert "pause_used" in columns
    assert "pause_deadline_at" in columns
    assert "requested_action" in columns
    assert "requested_action_at" in columns
    assert "claimed_by" in columns
    assert "claimed_at" in columns
    assert "claim_heartbeat_at" in columns


def test_leaderboard_entry_has_public_display_columns() -> None:
    columns = LeaderboardEntry.__table__.c
    assert "display_name" in columns
    assert "anonymous" in columns


def test_test_run_has_pause_timeout_lookup_index() -> None:
    indexes = {
        index.name: tuple(column.name for column in index.columns)
        for index in EvaluationRunModel.__table__.indexes
    }
    assert "ix_test_runs_status_pause_deadline_at" in indexes
    assert indexes["ix_test_runs_status_pause_deadline_at"] == ("status", "pause_deadline_at")


def test_sample_execution_has_updated_at() -> None:
    assert "updated_at" in SampleExecution.__table__.c


def test_run_dataset_model_exists() -> None:
    columns = RunDataset.__table__.c
    assert "run_id" in columns
    assert "dataset_code" in columns
    assert "dataset_name" in columns
    assert "order_no" in columns
    assert "status" in columns
    assert "total_samples" in columns
    assert "completed_samples" in columns
    assert "created_at" in columns
    assert "updated_at" in columns
    assert "started_at" in columns
    assert "finished_at" in columns


def test_risk_subtype_code_is_globally_unique() -> None:
    assert RiskSubtype.__table__.c.code.unique is True
    assert "description" not in RiskSubtype.__table__.c


def test_sample_oracle_updated_at_has_server_default() -> None:
    column = SampleOracle.__table__.c.updated_at
    assert column.server_default is not None
    assert column.nullable is False
