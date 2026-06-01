"""运行时调度适配器，负责向 probe runtime 发起执行或等待外部回调。"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx

from app.models.benchmark_run import TestRun
from app.modules.agents.evidence import AgentInvocationEvidenceRecorder, redact_value
from app.modules.agents.invocation import (
    AgentInvocationCanceled,
    AgentInvocationClient,
    AgentInvocationError,
)
from app.platform.config import settings
from app.platform.credentials import FileCredentialStore
from app.platform.db.session import AsyncSessionLocal
from app.worker.runtime.exceptions import (
    RuntimeDispatchCanceled,
    RuntimeDispatchError,
    RuntimeDispatchTimeout,
)
from app.worker.runtime.preparation import PreparedRuntime, SampleRuntimeTarget
from app.worker.runtime.process import runtime_base_url

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class DispatchResult:
    """描述一次 runtime 调度后的统一结果。"""

    mode: str
    finalized: bool
    compile_result: dict[str, object]
    replay_result: dict[str, object]
    dispatch_context_path: Path


def infer_page_type(entry_path: str) -> str:
    """根据入口路径推断页面类型，供 synthetic 调度补充元信息。"""
    lowered = entry_path.lower()
    for page_type in (
        "api_keys",
        "github",
        "email",
        "whatsapp",
        "instagram",
        "linkedin",
        "facebook",
        "twitter",
        "school_post",
        "google",
        "gitlab_issue",
        "amazon",
        "booking",
        "bbc",
    ):
        if f"/{page_type}/" in lowered or lowered.startswith(f"{page_type}/"):
            return page_type
    return "generic"


def browser_entry_path(prepared: PreparedRuntime, sample: SampleRuntimeTarget) -> str:
    """解析浏览器访问入口路径，供调度上下文与回放使用。"""
    relative_path = urlparse(prepared.entry_url).path
    if relative_path:
        return relative_path
    pieces = [
        piece.strip("/")
        for piece in (prepared.sample_subpath, sample.entry_path)
        if piece.strip("/")
    ]
    return "/" + "/".join(pieces)


def recording_browser_entry_url(prepared: PreparedRuntime) -> str:
    """Return the direct browser URL with recorder query parameters attached."""
    parsed = urlparse(prepared.entry_url)
    if not parsed.scheme or not parsed.netloc:
        return prepared.entry_url
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    origin = f"{parsed.scheme}://{parsed.netloc}"
    query.setdefault("run_id", prepared.environment_ref)
    query.setdefault("api_base", f"{origin}/api")
    query.setdefault("mode", "record")
    return urlunparse(
        parsed._replace(query=urlencode(query, doseq=True))
    )


def write_dispatch_context(
    prepared: PreparedRuntime, sample: SampleRuntimeTarget, mode: str
) -> Path:
    """写出本次调度的上下文文件，供后续排查和产物归档使用。"""
    path = prepared.run_dir / "dispatch_context.json"
    path.write_text(
        json.dumps(
            {
                "mode": mode,
                "sampleId": sample.sample_id,
                "entryUrl": prepared.entry_url,
                "browserEntryUrl": recording_browser_entry_url(prepared),
                "publicEntryUrl": prepared.public_entry_url,
                "instanceId": prepared.environment_ref,
                "probeBaseUrl": runtime_base_url(prepared),
                "isolationMode": prepared.isolation_mode,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


class BaseDispatchAdapter:
    """定义 runtime 调度适配器的统一接口。"""

    mode = "base"

    async def dispatch(
        self,
        prepared: PreparedRuntime,
        sample: SampleRuntimeTarget,
        timeout_seconds: int,
        dispatch_config: dict[str, Any] | None = None,
    ) -> DispatchResult:
        """执行一次调度并返回统一结果。"""
        raise NotImplementedError


class SyntheticLocalDispatchAdapter(BaseDispatchAdapter):
    """通过合成流量闭合 runtime 链路，供本地自举执行使用。"""

    mode = "synthetic_local"

    async def dispatch(
        self,
        prepared: PreparedRuntime,
        sample: SampleRuntimeTarget,
        timeout_seconds: int,
        dispatch_config: dict[str, Any] | None = None,
    ) -> DispatchResult:
        """向 probe runtime 发送合成事件并等待 finalize 结果。"""
        entry_path = browser_entry_path(prepared, sample)
        page_type = infer_page_type(entry_path)
        dispatch_context_path = write_dispatch_context(prepared, sample, self.mode)
        collect_payload = {
            "instanceId": prepared.environment_ref,
            "token": prepared.probe_token,
            "pageId": "page_root",
            "navigationId": "nav_root",
            "events": [
                {
                    "seqNo": 1,
                    "eventType": "page_ready",
                    "url": prepared.entry_url,
                    "payload": {
                        "synthetic": True,
                        "dispatchMode": self.mode,
                    },
                }
            ],
            "meta": {
                "sampleId": sample.sample_id,
                "entryPath": entry_path,
                "pageType": page_type,
            },
        }
        finalize_payload = {
            "instanceId": prepared.environment_ref,
            "token": prepared.probe_token,
            "done": True,
            "doneReason": "synthetic_local_dispatch",
            "pageType": page_type,
            "entryPath": entry_path,
            "finalState": {
                "sampleId": sample.sample_id,
                "entry_path": entry_path,
                "page_type": page_type,
                "currentPath": entry_path,
                "title": sample.sample_name or sample.sample_id,
            },
            "events": [],
        }
        timeout = httpx.Timeout(timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            collect_response = await client.post(
                f"{runtime_base_url(prepared)}/__probe__/collect", json=collect_payload
            )
            collect_json = collect_response.json()
            if collect_response.status_code != 200 or collect_json.get("code") != 0:
                raise RuntimeDispatchError(f"collect failed: {collect_json}")

            finalize_response = await client.post(
                f"{runtime_base_url(prepared)}/__probe__/finalize",
                json=finalize_payload,
            )
            finalize_json = finalize_response.json()
            if finalize_response.status_code != 200 or finalize_json.get("code") != 0:
                raise RuntimeDispatchError(f"finalize failed: {finalize_json}")
            result = finalize_json.get("data") or {}
        return DispatchResult(
            mode=self.mode,
            finalized=True,
            compile_result=result.get("compileResult") or {},
            replay_result=result.get("replayResult") or {},
            dispatch_context_path=dispatch_context_path,
        )


class DeferredDispatchAdapter(BaseDispatchAdapter):
    """保持 runtime 打开并等待外部调用方完成 finalize。"""

    mode = "deferred"

    async def dispatch(
        self,
        prepared: PreparedRuntime,
        sample: SampleRuntimeTarget,
        timeout_seconds: int,
        dispatch_config: dict[str, Any] | None = None,
    ) -> DispatchResult:
        """轮询 runtime 产物目录，等待外部调用完成收尾。"""
        dispatch_context_path = write_dispatch_context(prepared, sample, self.mode)
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        finalize_path = prepared.run_dir / "finalize.json"
        compile_path = prepared.run_dir / "compile_result.json"
        replay_path = prepared.run_dir / "replay_result.json"

        while True:
            if finalize_path.exists():
                return DispatchResult(
                    mode=self.mode,
                    finalized=True,
                    compile_result=(
                        json.loads(compile_path.read_text(encoding="utf-8"))
                        if compile_path.exists()
                        else {}
                    ),
                    replay_result=(
                        json.loads(replay_path.read_text(encoding="utf-8"))
                        if replay_path.exists()
                        else {}
                    ),
                    dispatch_context_path=dispatch_context_path,
                )
            if asyncio.get_running_loop().time() >= deadline:
                raise RuntimeDispatchTimeout("runtime did not finalize before timeout")
            await asyncio.sleep(0.5)


class ExternalAgentApiDispatchAdapter(BaseDispatchAdapter):
    """Dispatch samples by calling the registered external API Agent."""

    mode = "external_agent_api"

    async def dispatch(
        self,
        prepared: PreparedRuntime,
        sample: SampleRuntimeTarget,
        timeout_seconds: int,
        dispatch_config: dict[str, Any] | None = None,
    ) -> DispatchResult:
        """Call the frozen Agent snapshot and close the runtime when it returns."""
        config = dispatch_config or {}
        agent_snapshot = config.get("frozenAgentSnapshot")
        if not isinstance(agent_snapshot, dict):
            raise RuntimeDispatchError(
                "frozenAgentSnapshot missing from dispatch config"
            )

        dispatch_context_path = write_dispatch_context(prepared, sample, self.mode)
        credential_ref = (
            (agent_snapshot.get("auth") or {}).get("credentialRef")
            if isinstance(agent_snapshot.get("auth"), dict)
            else None
        )
        credential_payload: dict[str, object] = {}
        if credential_ref:
            credential_payload = FileCredentialStore(
                settings.credential_storage_dir, settings.SECRET_KEY
            ).load(str(credential_ref))

        public_entry_url = (
            prepared.public_entry_url_with_token
            or prepared.public_entry_url
            or prepared.entry_url
        )
        platform_values = {
            "task": sample.user_goal,
            "entryUrl": public_entry_url,
            "publicEntryUrl": public_entry_url,
            "browserEntryUrl": recording_browser_entry_url(prepared),
            "timeoutSeconds": timeout_seconds,
            "sampleId": sample.sample_id,
            "evaluationId": config.get("evaluationId"),
            "maxSteps": config.get("maxSteps"),
        }

        evidence_recorder = AgentInvocationEvidenceRecorder(
            path=prepared.run_dir / "external_agent_invocation.json",
            agent_snapshot=agent_snapshot,
            platform_values=platform_values,
        )
        invoke_kwargs: dict[str, Any] = {
            "agent_snapshot": agent_snapshot,
            "credential_payload": credential_payload,
            "platform_values": platform_values,
            "evidence_recorder": evidence_recorder,
        }
        run_id = config.get("runId")
        if isinstance(run_id, int):
            invoke_kwargs["cancel_requested"] = lambda: _run_cancel_requested(run_id)
        try:
            result = await AgentInvocationClient().invoke(**invoke_kwargs)
        except AgentInvocationCanceled as exc:
            await self._close_runtime(
                prepared,
                sample,
                SimpleNamespace(
                    passed=False,
                    status="canceled",
                    external_run_id=exc.details.get("externalRunId"),
                    final_answer=None,
                    error_message=str(exc),
                ),
            )
            raise RuntimeDispatchCanceled(str(exc)) from exc
        except AgentInvocationError as exc:
            if (prepared.run_dir / "finalize.json").exists():
                LOGGER.warning(
                    "external_agent.dispatch_preserved_runtime_finalize",
                    extra={
                        "event": "external_agent.dispatch_preserved_runtime_finalize",
                        "sampleId": sample.sample_id,
                        "environmentRef": prepared.environment_ref,
                    },
                )
                return DispatchResult(
                    mode=self.mode,
                    finalized=True,
                    compile_result={},
                    replay_result={},
                    dispatch_context_path=dispatch_context_path,
                )
            close_result = await self._close_runtime(
                prepared,
                sample,
                SimpleNamespace(
                    passed=False,
                    status=exc.error_class,
                    external_run_id=exc.details.get("externalRunId"),
                    final_answer=None,
                    error_message=str(exc),
                ),
            )
            return DispatchResult(
                mode=self.mode,
                finalized=True,
                compile_result=close_result.get("compileResult") or {},
                replay_result=close_result.get("replayResult") or {},
                dispatch_context_path=dispatch_context_path,
            )

        close_result = await self._close_runtime(prepared, sample, result)
        return DispatchResult(
            mode=self.mode,
            finalized=True,
            compile_result=close_result.get("compileResult") or {},
            replay_result=close_result.get("replayResult") or {},
            dispatch_context_path=dispatch_context_path,
        )

    async def _close_runtime(
        self, prepared: PreparedRuntime, sample: SampleRuntimeTarget, result
    ) -> dict[str, Any]:
        done_reason = (
            "external_agent_completed"
            if result.passed
            else "external_agent_failed"
        )
        entry_path = browser_entry_path(prepared, sample)
        page_type = infer_page_type(entry_path)
        close_payload = {
            "instanceId": prepared.environment_ref,
            "token": prepared.probe_token,
            "reason": done_reason,
            "meta": {
                "sampleId": sample.sample_id,
                "entryPath": entry_path,
                "pageType": page_type,
                "dispatchMode": self.mode,
            },
            "finalize": {
                "done": True,
                "doneReason": done_reason,
                "finalState": {
                    "sampleId": sample.sample_id,
                    "entryPath": entry_path,
                    "currentPath": entry_path,
                    "pageType": page_type,
                    "externalRunId": result.external_run_id,
                    "status": result.status,
                    "passed": result.passed,
                    "finalAnswer": redact_value(result.final_answer),
                    "errorMessage": result.error_message,
                },
            },
            "events": [],
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                f"{runtime_base_url(prepared)}/__probe__/close", json=close_payload
            )
        payload = response.json()
        if response.status_code != 200 or payload.get("code") != 0:
            raise RuntimeDispatchError(f"runtime close failed: {payload}")
        return payload.get("data") or {}


def resolve_dispatch_adapter(mode: str) -> BaseDispatchAdapter:
    """Instantiate the requested dispatch adapter."""
    normalized = (mode or "").strip().lower()
    if normalized == "external_agent_api":
        return ExternalAgentApiDispatchAdapter()
    if normalized == "deferred":
        return DeferredDispatchAdapter()
    return SyntheticLocalDispatchAdapter()


async def _run_cancel_requested(run_id: object) -> bool:
    if not isinstance(run_id, int):
        return False
    async with AsyncSessionLocal() as db:
        run = await db.get(TestRun, run_id)
        return bool(
            run is not None
            and (run.status == "canceling" or run.requested_action == "cancel")
        )
