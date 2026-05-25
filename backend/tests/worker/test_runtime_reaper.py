from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.models.benchmark import BenchmarkSample
from app.models.benchmark_run import (
    RunSample,
    RuntimeSession,
    SampleExecution,
    TestRun as RunModel,
)
from app.modules.runtime_gateway.session_store import hash_runtime_token
from app.platform.db.session import AsyncSessionLocal, engine as async_engine
from app.worker.runtime import reaper as runtime_reaper
from app.worker.runtime.reaper import ManagedRuntimeContainer, reap_runtime_containers_once

pytestmark = pytest.mark.worker


@pytest_asyncio.fixture(autouse=True)
async def isolate_async_engine_pool_for_event_loop():
    await async_engine.dispose()
    yield
    await async_engine.dispose()


def _seed_execution_with_session(
    api_db_helper,
    *,
    active_expires_at: datetime,
    expired_expires_at: datetime,
) -> tuple[int, int]:
    user_id, _ = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_runtime_reaper_user",
        email=f"{api_db_helper.prefix}_runtime_reaper_user@example.com",
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
        active_execution = SampleExecution(
            run_id=run.id,
            run_sample_id=run_sample.id,
            sample_id_ref=sample.id,
            status="executing",
            retry_no=0,
        )
        expired_execution = SampleExecution(
            run_id=run.id,
            run_sample_id=run_sample.id,
            sample_id_ref=sample.id,
            status="executing",
            retry_no=1,
        )
        session.add_all([active_execution, expired_execution])
        session.flush()
        session.add_all(
            [
            RuntimeSession(
                sample_execution_id=active_execution.id,
                run_id=run.id,
                environment_ref=f"rt_{active_execution.id}_active",
                internal_base_url=(
                    f"http://asp-runtime-rt_{active_execution.id}_active:8000"
                ),
                public_entry_url=(
                    f"https://platform.example.com/runtime/tasks/{active_execution.id}/"
                ),
                token_hash=hash_runtime_token("runtime-token"),
                expires_at=active_expires_at,
                status="active",
            ),
            RuntimeSession(
                sample_execution_id=expired_execution.id,
                run_id=run.id,
                environment_ref=f"rt_{expired_execution.id}_expired",
                internal_base_url=(
                    f"http://asp-runtime-rt_{expired_execution.id}_expired:8000"
                ),
                public_entry_url=(
                    f"https://platform.example.com/runtime/tasks/{expired_execution.id}/"
                ),
                token_hash=hash_runtime_token("runtime-token"),
                expires_at=expired_expires_at,
                status="active",
            ),
            ]
        )
        session.commit()
        return active_execution.id, expired_execution.id


@pytest.mark.asyncio
async def test_worker_runtime_reaper_stops_only_containers_without_active_session(
    api_db_helper,
    monkeypatch,
) -> None:
    now = datetime.now(timezone.utc)
    active_execution_id, expired_execution_id = _seed_execution_with_session(
        api_db_helper,
        active_expires_at=now + timedelta(minutes=10),
        expired_expires_at=now - timedelta(minutes=1),
    )
    orphan_execution_id = expired_execution_id + 100_000
    stopped: list[str] = []

    async def fake_list_managed_runtime_containers():
        return [
            ManagedRuntimeContainer(
                container_id="container-active",
                sample_execution_id=active_execution_id,
                environment_ref=f"rt_{active_execution_id}_active",
            ),
            ManagedRuntimeContainer(
                container_id="container-expired",
                sample_execution_id=expired_execution_id,
                environment_ref=f"rt_{expired_execution_id}_expired",
            ),
            ManagedRuntimeContainer(
                container_id="container-orphan",
                sample_execution_id=orphan_execution_id,
                environment_ref=f"rt_{orphan_execution_id}_orphan",
            ),
        ]

    async def fake_stop_runtime_container(container_id: str) -> None:
        stopped.append(container_id)

    monkeypatch.setattr(
        runtime_reaper,
        "list_managed_runtime_containers",
        fake_list_managed_runtime_containers,
    )
    monkeypatch.setattr(
        runtime_reaper,
        "stop_runtime_container",
        fake_stop_runtime_container,
    )
    monkeypatch.setattr(
        runtime_reaper.settings,
        "WORKER_RUNTIME_LAUNCH_MODE",
        "docker",
    )
    monkeypatch.setattr(
        runtime_reaper.settings,
        "RUNTIME_CONTAINER_REAPER_ENABLED",
        True,
        raising=False,
    )

    async with AsyncSessionLocal() as db:
        stopped_count = await reap_runtime_containers_once(db)

    with api_db_helper.session() as session:
        expired_row = session.execute(
            select(RuntimeSession).where(
                RuntimeSession.sample_execution_id == expired_execution_id
            )
        ).scalar_one()

    assert stopped_count == 2
    assert stopped == ["container-expired", "container-orphan"]
    assert expired_row.status == "expired"
    assert expired_row.revoked_at is not None
    await async_engine.dispose()
