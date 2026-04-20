from __future__ import annotations

import asyncio
import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from app.worker.runtime import (
    collect_artifacts,
    launch_runtime,
    prepare_runtime_workspace,
    resolve_dispatch_adapter,
    stop_runtime,
)
from app.worker.runtime import preparation as runtime_preparation
from app.worker.runtime.ports import allocate_tcp_port
from app.worker.runtime.preparation import (
    SampleRuntimeTarget,
    build_environment_ref,
    build_probe_token,
)


pytestmark = pytest.mark.worker


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
        json.dumps({"sample_id": "Sample_1", "user_goal": "open the page"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    runtime_root = subtype_root / "agent_runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "compiler.py").write_text(
        textwrap.dedent(
            """\
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
            """
        ),
        encoding="utf-8",
    )
    (runtime_root / "replay.py").write_text(
        textwrap.dedent(
            """\
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
            """
        ),
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
        result = await resolve_dispatch_adapter("synthetic_local").dispatch(prepared, sample, timeout_seconds=10)
    finally:
        await stop_runtime(handle)

    assert (prepared.run_dir / "meta.json").exists()
    assert (prepared.run_dir / "events.jsonl").exists()
    assert (prepared.run_dir / "finalize.json").exists()
    assert (prepared.run_dir / "compile_result.json").exists()
    assert (prepared.run_dir / "replay_result.json").exists()
    assert result.finalized is True

    artifact_types = {artifact.artifact_type for artifact in collect_artifacts(prepared)}
    assert "runtime_meta" in artifact_types
    assert "event_log" in artifact_types
    assert "compile_result" in artifact_types
    assert "replay_result" in artifact_types
    assert "replay_report" in artifact_types

