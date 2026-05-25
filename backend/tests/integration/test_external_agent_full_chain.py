from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.models.benchmark_run import (
    ExecutionArtifact,
    ExecutionSummary,
    RunDataset,
    RunReport,
    SampleExecution,
    TestRun as RunModel,
)
from app.modules.agents.repository import AgentRepository
from app.modules.agents.schemas import AgentCreateRequest, AgentVerificationRequest
from app.modules.agents.service import AgentService
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import RegisterRequest
from app.modules.auth.service import AuthService
from app.modules.evaluations.repository import EvaluationRepository
from app.modules.evaluations.schemas import EvaluationCreateRequest
from app.modules.evaluations.service import EvaluationService
from app.platform.config import settings
from app.platform.db.session import AsyncSessionLocal, engine as async_engine
from app.worker import execution as worker_execution
from app.worker.sample_claims import claim_next_sample
from app.worker.sample_scheduler import finalize_ready_runs_once, release_ready_samples_once
from app.worker.sample_worker import _process_sample_safely
from app.worker.runtime import preparation as runtime_preparation
from app.worker.runtime.ports import allocate_tcp_port


@pytest_asyncio.fixture(autouse=True)
async def isolate_async_engine_pool_for_event_loop() -> AsyncIterator[None]:
    await async_engine.dispose()
    yield
    await async_engine.dispose()


@contextmanager
def mock_agent_server(port: int) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path != "/health":
                self.send_error(404)
                return
            self._send_json({"ok": True})

        def do_POST(self) -> None:
            if self.path != "/run":
                self.send_error(404)
                return
            content_length = int(self.headers.get("content-length") or "0")
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            self._send_json(
                {
                    "status": "completed",
                    "answer": {
                        "prompt": payload.get("prompt"),
                        "url": payload.get("url"),
                        "sampleId": payload.get("sample_id"),
                        "evaluationId": payload.get("evaluation_id"),
                    },
                    "error": None,
                }
            )

        def log_message(self, *_args) -> None:
            return None

        def _send_json(self, payload: dict[str, object]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def write_runtime_sample_tree(data_root: Path, prefix: str) -> None:
    sample_root = data_root / prefix / "resource"
    sample_root.mkdir(parents=True, exist_ok=True)
    (sample_root / "index.html").write_text(
        "<!doctype html><html><head><title>Full Chain</title></head><body>ok</body></html>",
        encoding="utf-8",
    )
    (sample_root / "task.json").write_text(
        json.dumps(
            {"sample_id": f"{prefix}_sample", "user_goal": "完成正常任务"},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (data_root / prefix / "agent_runtime").mkdir(parents=True, exist_ok=True)


@pytest.mark.db
@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_submission_worker_external_agent_runtime_full_chain(
    api_db_helper, tmp_path: Path, monkeypatch
) -> None:
    dataset_code = api_db_helper.seed_dataset()
    data_root = tmp_path / "datasets"
    runtime_root = tmp_path / "runtime"
    write_runtime_sample_tree(data_root, api_db_helper.prefix)

    monkeypatch.setattr(settings, "DATASET_ROOT_DIR", str(data_root))
    monkeypatch.setattr(settings, "RUNTIME_ROOT_DIR", str(runtime_root))
    monkeypatch.setattr(settings, "AGENT_HTTP_ALLOW_PRIVATE_NETWORKS", True)
    monkeypatch.setattr(settings, "WORKER_NAMESPACE_ISOLATION_ENABLED", False)
    monkeypatch.setattr(settings, "SAMPLE_WORKER_MAX_ACTIVE_EXECUTIONS", 1)
    monkeypatch.setattr(
        worker_execution.settings, "WORKER_MAX_ACTIVE_RUNTIME_PROCESSES", 1
    )
    monkeypatch.setattr(runtime_preparation, "DATA_ROOT", data_root)

    mock_port = allocate_tcp_port("127.0.0.1")
    with mock_agent_server(mock_port) as agent_base_url:
        async with AsyncSessionLocal() as db:
            current_user = (
                await AuthService(AuthRepository(db)).register(
                    RegisterRequest.model_validate(
                        {
                            "username": f"{api_db_helper.prefix}_full_chain_user",
                            "email": f"{api_db_helper.prefix}_full_chain@example.com",
                            "password": "secret123",
                        }
                    )
                )
            ).user

            agent_service = AgentService(AgentRepository(db))
            create_agent_response = await agent_service.create_agent(
                AgentCreateRequest.model_validate(
                    {
                        "templateId": "http_submit_poll_basic",
                        "name": f"{api_db_helper.prefix} full chain agent",
                        "description": "full chain integration",
                        "invokeMode": "sync_response",
                        "connection": {
                            "baseUrl": agent_base_url,
                            "invokePath": "/run",
                            "requestTimeoutSeconds": 30,
                        },
                        "auth": {"type": "none", "config": {}},
                        "platformInputMapping": {
                            "task": "prompt",
                            "entryUrl": "url",
                            "timeoutSeconds": "timeout_sec",
                            "sampleId": "sample_id",
                            "evaluationId": "evaluation_id",
                            "maxSteps": "max_steps",
                        },
                        "taskRenderMode": "goal_only",
                        "customRequestBody": {"secret": "full-chain-secret"},
                        "requestOptions": {},
                        "platformOutputMapping": {
                            "status": "status",
                            "finalAnswer": "answer",
                            "errorMessage": "error",
                        },
                        "terminalStatuses": ["completed", "failed"],
                        "successStatuses": ["completed"],
                    }
                ),
                current_user,
            )
            agent_id = create_agent_response.agent_id

            verify_response = await agent_service.verify_agent(
                agent_id,
                AgentVerificationRequest(timeout_seconds=30),
                current_user,
            )
            assert verify_response.status == "active"

            evaluation_service = EvaluationService(EvaluationRepository(db))
            submit_response = await evaluation_service.create_evaluation(
                EvaluationCreateRequest.model_validate(
                    {
                        "submitMethod": "api",
                        "agentId": agent_id,
                        "parameters": {
                            "difficulty": 0.5,
                            "timeoutMinutes": 20,
                            "maxSteps": 30,
                        },
                        "leaderboardDisplayMode": "anonymous",
                        "datasetIds": [dataset_code],
                        "requestId": f"{api_db_helper.prefix}_full_chain_request",
                    }
                ),
                current_user,
            )
            evaluation_id = submit_response.evaluation_id

            run_id = (
                await db.execute(
                    select(RunModel.id).where(RunModel.public_id == evaluation_id)
                )
            ).scalar_one()

        async with AsyncSessionLocal() as db:
            assert await release_ready_samples_once(db) == 1

        async with AsyncSessionLocal() as db:
            claimed_execution = await claim_next_sample(db, "pytest-sample-worker")
            assert claimed_execution is not None

        await _process_sample_safely(
            claimed_execution.id,
            "pytest-sample-worker",
            claimed_execution.claim_token,
        )

        async with AsyncSessionLocal() as db:
            assert await finalize_ready_runs_once(db) == 1

        async with AsyncSessionLocal() as db:
            detail = await EvaluationService(
                EvaluationRepository(db)
            ).get_evaluation_detail(evaluation_id, current_user)

        assert detail.status == "completed"
        assert detail.final_report_available is True
        assert detail.progress.percent == 100

        with api_db_helper.session() as session:
            run = session.execute(
                select(RunModel).where(RunModel.public_id == evaluation_id)
            ).scalar_one()
            dataset = session.execute(
                select(RunDataset).where(RunDataset.run_id == run.id)
            ).scalar_one()
            execution = session.execute(
                select(SampleExecution).where(SampleExecution.run_id == run.id)
            ).scalar_one()
            artifacts = list(
                session.execute(
                    select(ExecutionArtifact).where(
                        ExecutionArtifact.sample_execution_id == execution.id
                    )
                ).scalars()
            )
            artifact_types = {artifact.artifact_type for artifact in artifacts}
            evidence_artifact = next(
                artifact
                for artifact in artifacts
                if artifact.artifact_type == "external_agent_invocation"
            )
            summary = session.execute(
                select(ExecutionSummary).where(
                    ExecutionSummary.sample_execution_id == execution.id
                )
            ).scalar_one()
            report = session.execute(
                select(RunReport).where(RunReport.run_id == run.id)
            ).scalar_one()

        assert run.status == "completed"
        assert dataset.status == "completed"
        assert execution.status == "done"
        assert execution.entry_url is not None
        assert execution.entry_url.startswith(
            f"{settings.PUBLIC_BASE_URL}/runtime/tasks/{execution.id}/"
        )
        assert "token=" not in execution.entry_url
        assert summary.final_label == "needs_review"
        assert report.report_status == "available"
        assert {
            "dispatch_context",
            "runtime_meta",
            "event_log",
            "finalize_payload",
            "analysis_result",
            "external_agent_invocation",
        }.issubset(artifact_types)
        evidence_relative_path = evidence_artifact.artifact_metadata["relativePath"]
        evidence_payload = json.loads(
            (Path(execution.work_dir) / evidence_relative_path).read_text(
                encoding="utf-8"
            )
        )
        evidence_text = json.dumps(evidence_payload, ensure_ascii=False)
        assert evidence_payload["agentId"] == agent_id
        assert evidence_payload["evaluationId"] == evaluation_id
        assert evidence_payload["sampleId"].endswith("_sample")
        assert evidence_payload["outcome"]["status"] == "completed"
        assert evidence_payload["httpCalls"][0]["responseStatusCode"] == 200
        request_body = evidence_payload["httpCalls"][0]["requestBodyPreview"]["body"]
        assert request_body["url"].startswith(
            f"{settings.PUBLIC_BASE_URL}/runtime/tasks/{execution.id}/"
        )
        assert "token=runtime-token" not in evidence_text
        assert "token=%5Bredacted%5D" in request_body["url"]
        assert "full-chain-secret" not in evidence_text
