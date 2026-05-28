from __future__ import annotations

from pathlib import Path


def test_observability_models_and_enums_are_registered() -> None:
    from app.models import AuditLog, SampleExecutionEvent
    from app.platform.observability import AuditActorType, SampleExecutionEventType

    assert SampleExecutionEvent.__tablename__ == "sample_execution_events"
    assert AuditLog.__tablename__ == "audit_logs"
    assert SampleExecutionEventType.EVALUATION_CREATED.value == "evaluation.created"
    assert SampleExecutionEventType.SAMPLE_CLAIMED.value == "sample.claimed"
    assert (
        SampleExecutionEventType.ORACLE_JUDGEMENT_FINISHED.value
        == "oracle.judgement.finished"
    )
    assert AuditActorType.API_KEY.value == "api_key"
    assert AuditActorType.ANONYMOUS.value == "anonymous"


def test_artifact_root_defaults_outside_project(monkeypatch) -> None:
    from app.platform.config import Settings

    monkeypatch.delenv("ARTIFACT_ROOT_DIR", raising=False)
    settings = Settings(ASP_DATA_ROOT="/mnt/asp", _env_file=None)

    assert settings.artifact_root == Path("/mnt/asp/artifacts")
