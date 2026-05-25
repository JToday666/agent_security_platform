from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.models.benchmark import BenchmarkSample
from app.models.benchmark_run import (
    TestRun as RunModel,
    RunSample,
    RuntimeSession,
    SampleExecution,
)
from app.modules.runtime_gateway.session_store import (
    RuntimeSessionView,
    authorize_runtime_request,
    build_public_runtime_url,
    close_runtime_session,
    create_runtime_session,
    expire_runtime_sessions_once,
    generate_runtime_token,
    hash_runtime_token,
    runtime_session_is_active,
    verify_runtime_token,
)
from app.platform.db.session import AsyncSessionLocal, engine


def test_runtime_token_hash_does_not_store_plain_token() -> None:
    token = generate_runtime_token()
    token_hash = hash_runtime_token(token)

    assert token not in token_hash
    assert verify_runtime_token(token, token_hash) is True
    assert verify_runtime_token(f"{token}x", token_hash) is False


def test_build_public_runtime_url_uses_gateway_prefix_and_keeps_entry_path(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.modules.runtime_gateway.session_store.settings.PUBLIC_BASE_URL",
        "https://platform.example.com/",
        raising=False,
    )

    url = build_public_runtime_url(
        sample_execution_id=123,
        internal_entry_url="http://asp-runtime-rt_123:8000/Sample_1/site/index.html?debug=1",
        token="runtime-token",
    )

    assert (
        url
        == "https://platform.example.com/runtime/tasks/123/Sample_1/site/index.html?debug=1&token=runtime-token"
    )


def test_runtime_session_active_requires_active_status_and_future_expiry() -> None:
    session = RuntimeSessionView(
        sample_execution_id=123,
        internal_base_url="http://asp-runtime-rt_123:8000",
        public_entry_url="https://platform.example.com/runtime/tasks/123/",
        token_hash=hash_runtime_token("runtime-token"),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        status="active",
    )

    assert runtime_session_is_active(session) is True

    session.status = "closed"
    assert runtime_session_is_active(session) is False

    session.status = "active"
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert runtime_session_is_active(session) is False


@pytest.mark.asyncio
async def test_runtime_session_db_lifecycle_hashes_token_and_revokes(
    api_db_helper, monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.modules.runtime_gateway.session_store.settings.PUBLIC_BASE_URL",
        "https://platform.example.com",
        raising=False,
    )
    user_id, _ = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_runtime_user",
        email=f"{api_db_helper.prefix}_runtime_user@example.com",
    )
    dataset_code = api_db_helper.seed_dataset()
    api_db_helper.seed_evaluation_run(
        user_id=user_id, dataset_code=dataset_code, status="executing"
    )
    with api_db_helper.session() as session:
        run = session.execute(
            select(RunModel).where(
                RunModel.public_id == f"eval_{api_db_helper.prefix}"
            )
        ).scalar_one()
        sample = session.execute(
            select(BenchmarkSample).where(
                BenchmarkSample.sample_id == f"{api_db_helper.prefix}_sample"
            )
        ).scalar_one()
        run_sample = RunSample(
            run_id=run.id,
            sample_id_ref=sample.id,
            order_no=1,
        )
        session.add(run_sample)
        session.flush()
        execution = SampleExecution(
            run_id=run.id,
            run_sample_id=run_sample.id,
            sample_id_ref=sample.id,
            status="executing",
            retry_no=0,
        )
        session.add(execution)
        session.commit()
        execution_id = execution.id
        run_id = run.id

    prepared = SimpleNamespace(
        execution_id=execution_id,
        run_id=run_id,
        environment_ref=f"rt_{execution_id}_test",
        entry_url="http://asp-runtime-test:8000/Sample_1/site/index.html",
        isolation_mode="docker",
        public_entry_url=None,
    )

    created = await create_runtime_session(
        prepared=prepared, run_id=run_id, timeout_seconds=60
    )

    with api_db_helper.session() as session:
        row = session.execute(
            select(RuntimeSession).where(
                RuntimeSession.sample_execution_id == execution_id
            )
        ).scalar_one()
        assert row.status == "active"
        assert row.token_hash != created.token
        assert created.token not in row.token_hash
        assert row.internal_base_url.startswith(
            f"http://asp-runtime-rt_{execution_id}_test"
        )
        assert "token=" not in row.public_entry_url
        assert row.public_entry_url == created.public_entry_url_without_token
        assert created.public_entry_url.startswith(row.public_entry_url)
        assert "token=" in created.public_entry_url

    loaded, token_source = await authorize_runtime_request(
        sample_execution_id=execution_id,
        query_token=created.token,
        cookie_token=None,
    )

    assert token_source == "query"
    assert loaded is not None
    assert loaded.internal_base_url.startswith(
        f"http://asp-runtime-rt_{execution_id}_test"
    )

    await close_runtime_session(execution_id, status="closed")

    loaded, token_source = await authorize_runtime_request(
        sample_execution_id=execution_id,
        query_token=created.token,
        cookie_token=None,
    )

    assert loaded is None
    assert token_source == "closed"
    await engine.dispose()


@pytest.mark.asyncio
async def test_runtime_session_reaper_expires_sessions_without_request(
    api_db_helper,
) -> None:
    user_id, _ = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_runtime_reaper_user",
        email=f"{api_db_helper.prefix}_runtime_reaper_user@example.com",
    )
    dataset_code = api_db_helper.seed_dataset()
    api_db_helper.seed_evaluation_run(
        user_id=user_id, dataset_code=dataset_code, status="executing"
    )
    expired_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    with api_db_helper.session() as session:
        run = session.execute(
            select(RunModel).where(
                RunModel.public_id == f"eval_{api_db_helper.prefix}"
            )
        ).scalar_one()
        sample = session.execute(
            select(BenchmarkSample).where(
                BenchmarkSample.sample_id == f"{api_db_helper.prefix}_sample"
            )
        ).scalar_one()
        run_sample = RunSample(
            run_id=run.id,
            sample_id_ref=sample.id,
            order_no=1,
        )
        session.add(run_sample)
        session.flush()
        execution = SampleExecution(
            run_id=run.id,
            run_sample_id=run_sample.id,
            sample_id_ref=sample.id,
            status="executing",
            retry_no=0,
        )
        session.add(execution)
        session.flush()
        session.add(
            RuntimeSession(
                sample_execution_id=execution.id,
                run_id=run.id,
                environment_ref=f"rt_{execution.id}_expired",
                internal_base_url=f"http://asp-runtime-rt_{execution.id}_expired:8000",
                public_entry_url=(
                    f"https://platform.example.com/runtime/tasks/{execution.id}/"
                ),
                token_hash=hash_runtime_token("runtime-token"),
                expires_at=expired_at,
                status="active",
            )
        )
        session.commit()
        execution_id = execution.id

    async with AsyncSessionLocal() as db:
        expired_count = await expire_runtime_sessions_once(db)

    with api_db_helper.session() as session:
        row = session.execute(
            select(RuntimeSession).where(
                RuntimeSession.sample_execution_id == execution_id
            )
        ).scalar_one()

    assert expired_count >= 1
    assert row.status == "expired"
    assert row.revoked_at is not None
    await engine.dispose()
