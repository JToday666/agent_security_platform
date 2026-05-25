from __future__ import annotations

import asyncio
import json
import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.worker.runtime import (
    collect_artifacts,
    launch_runtime,
    prepare_runtime_workspace,
    resolve_dispatch_adapter,
    stop_runtime,
)
from app.worker import execution
from app.worker.runtime import preparation as runtime_preparation
from app.worker.runtime.ports import allocate_tcp_port
from app.worker.runtime.preparation import (
    SampleRuntimeTarget,
    build_environment_ref,
    build_probe_token,
    resolve_sample_layout,
)

pytestmark = pytest.mark.worker


def test_resolve_sample_layout_uses_configured_dataset_root(tmp_path: Path) -> None:
    data_root = tmp_path / "datasets"
    subtype_root = data_root / "01_Confidentiality" / "A3_Address_and_Location_Leakage"
    sample_root = subtype_root / "EIA_A3_1_high"
    (sample_root / "site").mkdir(parents=True)
    (sample_root / "site" / "index.html").write_text(
        "<html></html>\n", encoding="utf-8"
    )
    (subtype_root / "agent_runtime").mkdir(parents=True)

    sample = SampleRuntimeTarget(
        sample_db_id=1,
        sample_id="EIA_A3_1_high",
        sample_name="EIA_A3_1_high",
        resource_path="01_Confidentiality/A3_Address_and_Location_Leakage/EIA_A3_1_high",
        entry_path="site/index.html",
        user_goal="open the page",
    )

    with patch.object(runtime_preparation.settings, "DATASET_ROOT_DIR", str(data_root)):
        sample_dir, scope_root, runtime_dir, sample_subpath = resolve_sample_layout(
            sample
        )

    assert sample_dir == sample_root.resolve()
    assert scope_root == subtype_root.resolve()
    assert runtime_dir == (subtype_root / "agent_runtime").resolve()
    assert sample_subpath.as_posix() == "EIA_A3_1_high"


def test_runtime_process_semaphore_tracks_configured_global_limit() -> None:
    with patch.object(execution.settings, "WORKER_MAX_ACTIVE_RUNTIME_PROCESSES", 3):
        first = execution._runtime_process_semaphore()
        second = execution._runtime_process_semaphore()

    assert first is second
    assert first._value == 3

    with patch.object(execution.settings, "WORKER_MAX_ACTIVE_RUNTIME_PROCESSES", 1):
        resized = execution._runtime_process_semaphore()

    assert resized is not first
    assert resized._value == 1


def test_resolve_browser_entry_host_prefers_configured_public_host() -> None:
    with (
        patch.object(execution.settings, "WORKER_RUNNER_HOST", "172.17.0.1"),
        patch.object(
            execution.settings,
            "WORKER_BROWSER_ENTRY_HOST",
            "host.docker.internal",
            create=True,
        ),
    ):
        assert execution._resolve_browser_entry_host() == "host.docker.internal"


def test_resolve_browser_entry_host_falls_back_to_runner_host() -> None:
    with (
        patch.object(execution.settings, "WORKER_RUNNER_HOST", "127.0.0.1"),
        patch.object(
            execution.settings, "WORKER_BROWSER_ENTRY_HOST", None, create=True
        ),
    ):
        assert execution._resolve_browser_entry_host() == "127.0.0.1"


@pytest.mark.asyncio
async def test_synthetic_local_dispatch_closes_runtime_loop(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    subtype_root = data_root / "Example_Subtype"
    sample_root = subtype_root / "Sample_1"
    (sample_root / "site").mkdir(parents=True, exist_ok=True)
    (sample_root / "site" / "index.html").write_text(
        "<!doctype html><html><head><title>Runtime Test</title></head><body>ok</body></html>",
        encoding="utf-8",
    )
    (sample_root / "task.json").write_text(
        json.dumps(
            {"sample_id": "Sample_1", "user_goal": "open the page"},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime_root = subtype_root / "agent_runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "compiler.py").write_text(
        textwrap.dedent("""\
            import argparse
            import json

            parser = argparse.ArgumentParser()
            parser.add_argument("--project-root", required=True)
            parser.add_argument("--run-id", required=True)
            args = parser.parse_args()
            print(json.dumps({
                "entry_path": "Sample_1/site/index.html",
                "page_type": "generic",
                "generated_script": "agent_runtime/generated/replay_from_events.py"
            }))
            """),
        encoding="utf-8",
    )
    (runtime_root / "replay.py").write_text(
        textwrap.dedent("""\
            import argparse
            import json
            from pathlib import Path

            parser = argparse.ArgumentParser()
            parser.add_argument("--project-root", required=True)
            parser.add_argument("--run-id", required=True)
            args = parser.parse_args()
            run_dir = Path(args.project_root) / "agent_runtime" / "runs" / args.run_id / "replay_artifacts"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "report.html").write_text("<html>report</html>", encoding="utf-8")
            print(json.dumps({
                "ok": True,
                "report": f"agent_runtime/runs/{args.run_id}/replay_artifacts/report.html"
            }))
            """),
        encoding="utf-8",
    )

    sample = SampleRuntimeTarget(
        sample_db_id=1,
        sample_id="Sample_1",
        sample_name="Sample_1",
        resource_path="Example_Subtype/Sample_1",
        entry_path="site/index.html",
        user_goal="open the page",
    )

    with patch.object(runtime_preparation, "DATA_ROOT", data_root):
        prepared = await asyncio.to_thread(
            prepare_runtime_workspace,
            sample,
            101,
            tmp_path / "runtime-workdir",
            "127.0.0.1",
            allocate_tcp_port("127.0.0.1"),
            build_environment_ref(101),
            build_probe_token(),
        )

    handle = await launch_runtime(prepared)
    try:
        result = await resolve_dispatch_adapter("synthetic_local").dispatch(
            prepared, sample, timeout_seconds=10
        )
    finally:
        await stop_runtime(handle)

    assert (prepared.run_dir / "meta.json").exists()
    assert (prepared.run_dir / "events.jsonl").exists()
    assert (prepared.run_dir / "finalize.json").exists()
    assert not (prepared.run_dir / "compile_result.json").exists()
    assert not (prepared.run_dir / "replay_result.json").exists()
    assert result.compile_result == {}
    assert result.replay_result == {}
    assert result.finalized is True

    artifact_types = {
        artifact.artifact_type for artifact in collect_artifacts(prepared)
    }
    assert "runtime_meta" in artifact_types
    assert "event_log" in artifact_types
    assert "compile_result" not in artifact_types
    assert "replay_result" not in artifact_types
    assert "replay_report" not in artifact_types


@pytest.mark.asyncio
async def test_external_agent_api_dispatch_closes_runtime_after_agent_success(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    subtype_root = data_root / "Example_Subtype"
    sample_root = subtype_root / "Sample_1"
    (sample_root / "site").mkdir(parents=True, exist_ok=True)
    (sample_root / "site" / "index.html").write_text(
        "<!doctype html><html><head><title>Runtime Test</title></head><body>ok</body></html>",
        encoding="utf-8",
    )

    runtime_root = subtype_root / "agent_runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "compiler.py").write_text(
        'print("{}")\n',
        encoding="utf-8",
    )
    (runtime_root / "replay.py").write_text(
        'print("{}")\n',
        encoding="utf-8",
    )

    sample = SampleRuntimeTarget(
        sample_db_id=1,
        sample_id="Sample_1",
        sample_name="Sample_1",
        resource_path="Example_Subtype/Sample_1",
        entry_path="site/index.html",
        user_goal="open the page",
    )

    with patch.object(runtime_preparation, "DATA_ROOT", data_root):
        prepared = await asyncio.to_thread(
            prepare_runtime_workspace,
            sample,
            202,
            tmp_path / "runtime-workdir",
            "127.0.0.1",
            allocate_tcp_port("127.0.0.1"),
            build_environment_ref(202),
            build_probe_token(),
        )

    class FakeInvocationClient:
        async def invoke(
            self, *, agent_snapshot, credential_payload, platform_values, evidence_recorder=None
        ):
            assert agent_snapshot["agentId"] == "agt_external"
            assert credential_payload == {}
            assert platform_values["task"] == "open the page"
            assert platform_values["entryUrl"].startswith("http://127.0.0.1:")
            assert evidence_recorder is not None
            evidence_recorder.path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "agentId": "agt_external",
                        "invokeMode": "sync_response",
                        "evaluationId": "eval_external",
                        "sampleId": "Sample_1",
                        "outcome": {"status": "completed"},
                        "httpCalls": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return SimpleNamespace(
                passed=True,
                status="completed",
                external_run_id="mock_run_202",
                final_answer={"ok": True},
                error_message=None,
            )

    handle = await launch_runtime(prepared)
    try:
        with patch(
            "app.worker.runtime.dispatch.AgentInvocationClient",
            return_value=FakeInvocationClient(),
        ):
            result = await resolve_dispatch_adapter("external_agent_api").dispatch(
                prepared,
                sample,
                timeout_seconds=10,
                dispatch_config={
                    "evaluationId": "eval_external",
                    "maxSteps": 12,
                    "frozenAgentSnapshot": {
                        "agentId": "agt_external",
                        "auth": {"type": "none"},
                    },
                },
            )
    finally:
        await stop_runtime(handle)

    finalize_payload = json.loads(
        (prepared.run_dir / "finalize.json").read_text(encoding="utf-8")
    )
    assert result.finalized is True
    assert finalize_payload["done"] is True
    assert finalize_payload["done_reason"] == "external_agent_completed"
    assert finalize_payload["final_state"]["external_run_id"] == "mock_run_202"
    assert finalize_payload["final_state"]["status"] == "completed"
    evidence = json.loads(
        (prepared.run_dir / "external_agent_invocation.json").read_text(encoding="utf-8")
    )
    assert evidence["agentId"] == "agt_external"
    assert evidence["outcome"]["status"] == "completed"
    artifact_types = {artifact.artifact_type for artifact in collect_artifacts(prepared)}
    assert "external_agent_invocation" in artifact_types


@pytest.mark.asyncio
async def test_external_agent_api_dispatch_closes_runtime_after_agent_terminal_failure(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    subtype_root = data_root / "Example_Subtype"
    sample_root = subtype_root / "Sample_1"
    (sample_root / "site").mkdir(parents=True, exist_ok=True)
    (sample_root / "site" / "index.html").write_text(
        "<!doctype html><html><head><title>Runtime Test</title></head><body>ok</body></html>",
        encoding="utf-8",
    )

    runtime_root = subtype_root / "agent_runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "compiler.py").write_text(
        'print("{}")\n',
        encoding="utf-8",
    )
    (runtime_root / "replay.py").write_text(
        'print("{}")\n',
        encoding="utf-8",
    )

    sample = SampleRuntimeTarget(
        sample_db_id=1,
        sample_id="Sample_1",
        sample_name="Sample_1",
        resource_path="Example_Subtype/Sample_1",
        entry_path="site/index.html",
        user_goal="open the page",
    )

    with patch.object(runtime_preparation, "DATA_ROOT", data_root):
        prepared = await asyncio.to_thread(
            prepare_runtime_workspace,
            sample,
            203,
            tmp_path / "runtime-workdir",
            "127.0.0.1",
            allocate_tcp_port("127.0.0.1"),
            build_environment_ref(203),
            build_probe_token(),
        )

    class FakeInvocationClient:
        async def invoke(
            self, *, agent_snapshot, credential_payload, platform_values, evidence_recorder=None
        ):
            return SimpleNamespace(
                passed=False,
                status="terminated",
                external_run_id="mock_run_203",
                final_answer={"reason": "agent stopped"},
                error_message="agent terminated",
            )

    handle = await launch_runtime(prepared)
    try:
        with patch(
            "app.worker.runtime.dispatch.AgentInvocationClient",
            return_value=FakeInvocationClient(),
        ):
            result = await resolve_dispatch_adapter("external_agent_api").dispatch(
                prepared,
                sample,
                timeout_seconds=10,
                dispatch_config={
                    "evaluationId": "eval_external",
                    "maxSteps": 12,
                    "frozenAgentSnapshot": {
                        "agentId": "agt_external",
                        "auth": {"type": "none"},
                    },
                },
            )
    finally:
        await stop_runtime(handle)

    finalize_payload = json.loads(
        (prepared.run_dir / "finalize.json").read_text(encoding="utf-8")
    )
    assert result.finalized is True
    assert finalize_payload["done"] is True
    assert finalize_payload["done_reason"] == "external_agent_failed"
    assert finalize_payload["final_state"]["external_run_id"] == "mock_run_203"
    assert finalize_payload["final_state"]["status"] == "terminated"
    assert finalize_payload["final_state"]["passed"] is False
    assert finalize_payload["final_state"]["error_message"] == "agent terminated"
