"""运行时调度适配器，负责向 probe runtime 发起执行或等待外部回调。"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.worker.runtime.exceptions import RuntimeDispatchError, RuntimeDispatchTimeout
from app.worker.runtime.preparation import PreparedRuntime, SampleRuntimeTarget
from app.worker.runtime.process import runtime_base_url


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
    pieces = [piece.strip("/") for piece in (prepared.sample_subpath, sample.entry_path) if piece.strip("/")]
    return "/" + "/".join(pieces)


def write_dispatch_context(prepared: PreparedRuntime, sample: SampleRuntimeTarget, mode: str) -> Path:
    """写出本次调度的上下文文件，供后续排查和产物归档使用。"""
    path = prepared.run_dir / "dispatch_context.json"
    path.write_text(
        json.dumps(
            {
                "mode": mode,
                "sampleId": sample.sample_id,
                "entryUrl": prepared.entry_url,
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
            collect_response = await client.post(f"{runtime_base_url(prepared)}/__probe__/collect", json=collect_payload)
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
    ) -> DispatchResult:
        """轮询 runtime 产物目录，等待外部调用完成收尾。"""
        dispatch_context_path = write_dispatch_context(prepared, sample, self.mode)
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        finalize_path = prepared.run_dir / "finalize.json"
        compile_path = prepared.run_dir / "compile_result.json"
        replay_path = prepared.run_dir / "replay_result.json"

        while True:
            if finalize_path.exists() and compile_path.exists() and replay_path.exists():
                return DispatchResult(
                    mode=self.mode,
                    finalized=True,
                    compile_result=json.loads(compile_path.read_text(encoding="utf-8")),
                    replay_result=json.loads(replay_path.read_text(encoding="utf-8")),
                    dispatch_context_path=dispatch_context_path,
                )
            if asyncio.get_running_loop().time() >= deadline:
                raise RuntimeDispatchTimeout("runtime did not finalize before timeout")
            await asyncio.sleep(0.5)


def resolve_dispatch_adapter(mode: str) -> BaseDispatchAdapter:
    """Instantiate the requested dispatch adapter."""
    normalized = (mode or "").strip().lower()
    if normalized == "deferred":
        return DeferredDispatchAdapter()
    return SyntheticLocalDispatchAdapter()
