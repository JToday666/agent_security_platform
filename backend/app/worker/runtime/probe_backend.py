from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

RUN_LOCKS: dict[str, Lock] = {}


class SafeStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: dict[str, Any]):  # type: ignore[override]
        try:
            return await super().get_response(path, scope)
        except OSError:
            return PlainTextResponse("Not Found", status_code=404)


def success_response(
    data: Any, message: str = "success", status_code: int = 200
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"code": 0, "data": data, "message": message}
    )


def error_response(message: str, status_code: int, code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "data": None, "message": message},
    )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_lock_for(run_id: str) -> Lock:
    lock = RUN_LOCKS.get(run_id)
    if lock is None:
        lock = Lock()
        RUN_LOCKS[run_id] = lock
    return lock


def parse_payload(raw: bytes) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=400, detail=f"invalid json payload: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be a JSON object")
    return payload


def ensure_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_key(raw_key: str) -> str:
    parts: list[str] = []
    buffer: list[str] = []
    for char in raw_key:
        if char in {"-", " "}:
            if buffer:
                parts.append("".join(buffer))
                buffer = []
            continue
        if char.isupper() and buffer:
            parts.append("".join(buffer))
            buffer = [char.lower()]
            continue
        buffer.append(char.lower())
    if buffer:
        parts.append("".join(buffer))
    return "_".join(part for part in parts if part)


def normalize_mapping(raw: dict[str, Any] | None) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in (raw or {}).items():
        normalized[canonical_key(str(key))] = value
    return normalized


def normalize_meta(raw: dict[str, Any] | None) -> dict[str, Any]:
    meta = normalize_mapping(raw)
    if "sample_id" not in meta and meta.get("sample"):
        meta["sample_id"] = meta["sample"]
    return {
        key: value for key, value in meta.items() if value not in (None, "", [], {})
    }


def normalize_event(event: Any, page_id: str, navigation_id: str) -> dict[str, Any]:
    if not isinstance(event, dict):
        return {"raw_event": event}
    normalized = normalize_mapping(event)
    if "event_type" in normalized and "type" not in normalized:
        normalized["type"] = normalized.pop("event_type")
    if "seq_no" in normalized and "seq" not in normalized:
        normalized["seq"] = normalized.pop("seq_no")
    if "payload" in normalized and "extra" not in normalized:
        normalized["extra"] = normalized.pop("payload")
    element_meta = normalize_mapping(normalized.pop("element_meta", None))
    selector = normalized.pop("selector", "")
    if element_meta or selector:
        target = normalize_mapping(
            normalized.get("target")
            if isinstance(normalized.get("target"), dict)
            else {}
        )
        if selector and "selector" not in target:
            target["selector"] = selector
        target.update(element_meta)
        normalized["target"] = target
    if "url" in normalized and "page" not in normalized:
        raw_url = str(normalized["url"] or "")
        normalized["page"] = {
            "url": raw_url,
            "path": urlparse(raw_url).path,
            "title": "",
        }
    if page_id:
        normalized["page_id"] = page_id
    if navigation_id:
        normalized["navigation_id"] = navigation_id
    return normalized


def event_dedupe_key(run_id: str, page_id: str, event: dict[str, Any]) -> str | None:
    seq = event.get("seq")
    if seq in (None, ""):
        return None
    clean_page_id = page_id or str(event.get("page_id") or "")
    if not clean_page_id:
        return None
    return f"{run_id}:{clean_page_id}:{seq}"


def merge_meta(
    run_dir: Path, run_id: str, updates: dict[str, Any] | None = None
) -> dict[str, Any]:
    meta_path = run_dir / "meta.json"
    meta = ensure_json(
        meta_path,
        {
            "run_id": run_id,
            "instance_id": run_id,
            "created_at": utc_now_iso(),
            "total_events": 0,
        },
    )
    clean_updates = {
        key: value
        for key, value in (updates or {}).items()
        if value not in (None, "", [], {})
    }
    meta.update(clean_updates)
    meta["updated_at"] = utc_now_iso()
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta


def append_events(
    run_dir: Path,
    run_id: str,
    events: list[Any],
    page_id: str = "",
    navigation_id: str = "",
    meta_update: dict[str, Any] | None = None,
) -> tuple[int, int]:
    if not isinstance(events, list):
        raise HTTPException(status_code=400, detail="events must be a list")

    meta = merge_meta(run_dir, run_id, meta_update)
    jsonl_path = run_dir / "events.jsonl"
    dedupe_path = run_dir / "event_dedupe.json"
    seen_keys = set(ensure_json(dedupe_path, []))
    accepted_count = 0

    if events:
        with jsonl_path.open("a", encoding="utf-8") as handle:
            for raw_event in events:
                event = normalize_event(
                    raw_event, page_id=page_id, navigation_id=navigation_id
                )
                dedupe_key = event_dedupe_key(run_id, page_id, event)
                if dedupe_key and dedupe_key in seen_keys:
                    continue
                if dedupe_key:
                    seen_keys.add(dedupe_key)
                accepted_count += 1
                event["server_received_at"] = utc_now_iso()
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    else:
        jsonl_path.touch(exist_ok=True)

    dedupe_path.write_text(
        json.dumps(sorted(seen_keys), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    meta["total_events"] = int(meta.get("total_events", 0)) + accepted_count
    meta["updated_at"] = utc_now_iso()
    (run_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return accepted_count, int(meta["total_events"])


def is_finalized(run_dir: Path) -> bool:
    return (run_dir / "finalize.json").exists()


def normalize_finalize_payload(
    payload: dict[str, Any], fallback_reason: str | None = None
) -> dict[str, Any]:
    normalized = normalize_mapping(payload)
    if "done_reason" not in normalized and fallback_reason:
        normalized["done_reason"] = fallback_reason
    if "final_state" not in normalized and isinstance(normalized.get("state"), dict):
        normalized["final_state"] = normalize_mapping(normalized["state"])
    if "final_state" in normalized and isinstance(normalized["final_state"], dict):
        normalized["final_state"] = normalize_mapping(normalized["final_state"])
    return normalized


def run_json_tool(project_root: Path, script_name: str, run_id: str) -> dict[str, Any]:
    script_path = project_root / "agent_runtime" / script_name
    command = [
        sys.executable,
        str(script_path),
        "--project-root",
        str(project_root),
        "--run-id",
        run_id,
    ]
    completed = subprocess.run(
        command,
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    if stdout:
        try:
            payload = json.loads(stdout)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass
    if completed.returncode != 0:
        return {
            "ok": False,
            "run_id": run_id,
            "error": stderr
            or stdout
            or f"{script_name} exited with code {completed.returncode}",
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }
    return {"ok": True, "run_id": run_id, "stdout": stdout, "stderr": stderr}


def run_compiler(project_root: Path, run_id: str) -> dict[str, Any]:
    run_dir = project_root / "agent_runtime" / "runs" / run_id
    generated_manifest = run_dir / "generated" / "manifest.json"
    result = run_json_tool(project_root, "compiler.py", run_id)
    if isinstance(result, dict) and result.get("entry_path"):
        return result
    if generated_manifest.exists():
        return ensure_json(generated_manifest, {})
    if not result.get("ok", False):
        error_text = (
            result.get("stderr")
            or result.get("stdout")
            or result.get("error")
            or "unknown compiler failure"
        )
        (run_dir / "compile_error.txt").write_text(str(error_text), encoding="utf-8")
    return result


def maybe_auto_replay(project_root: Path, run_id: str) -> dict[str, Any]:
    run_dir = project_root / "agent_runtime" / "runs" / run_id
    result = run_json_tool(project_root, "replay.py", run_id)
    if not result.get("ok", False):
        error_text = (
            result.get("traceback")
            or result.get("stderr")
            or result.get("stdout")
            or result.get("error")
            or "unknown replay failure"
        )
        (run_dir / "auto_replay_error.txt").write_text(
            str(error_text), encoding="utf-8"
        )
    return result


def write_finalize(
    project_root: Path,
    run_dir: Path,
    run_id: str,
    payload: dict[str, Any],
    meta_update: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    finalize_path = run_dir / "finalize.json"

    merge_meta(run_dir, run_id, meta_update)

    payload = dict(payload)
    payload["run_id"] = run_id
    payload["instance_id"] = run_id
    payload["server_finalized_at"] = utc_now_iso()
    finalize_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {}, {}


def load_probe_script() -> str:
    return (Path(__file__).resolve().parent / "web" / "probe.js").read_text(
        encoding="utf-8"
    )


def build_probe_config(
    instance_id: str, probe_token: str, flush_interval_ms: int, max_batch_size: int
) -> dict[str, Any]:
    return {
        "instanceId": instance_id,
        "token": probe_token,
        "collectUrl": "/__probe__/collect",
        "finalizeUrl": "/__probe__/finalize",
        "closeUrl": "/__probe__/close",
        "flushIntervalMs": flush_interval_ms,
        "maxBatchSize": max_batch_size,
    }


def inject_probe_assets(html_text: str, probe_config: dict[str, Any]) -> str:
    injection = (
        "<script>"
        f"window.__PROBE_CONFIG__ = {json.dumps(probe_config, ensure_ascii=False, indent=2)};"
        "</script>\n"
        '<script src="/__probe__/probe.js"></script>\n'
    )
    lowered = html_text.lower()
    if "</head>" in lowered:
        head_index = lowered.rfind("</head>")
        return html_text[:head_index] + injection + html_text[head_index:]
    if "</body>" in lowered:
        body_index = lowered.rfind("</body>")
        return html_text[:body_index] + injection + html_text[body_index:]
    return injection + html_text


def ensure_instance(
    payload: dict[str, Any], instance_id: str, probe_token: str
) -> tuple[str, str]:
    incoming_instance_id = str(
        payload.get("instanceId") or payload.get("instance_id") or instance_id
    ).strip()
    incoming_token = str(payload.get("token") or probe_token).strip()
    if incoming_instance_id != instance_id:
        raise HTTPException(status_code=404, detail="unknown probe instance")
    if probe_token and incoming_token != probe_token:
        raise HTTPException(status_code=403, detail="invalid probe token")
    return incoming_instance_id, incoming_token


def create_app(
    project_root: Path,
    *,
    instance_id: str,
    probe_token: str,
    flush_interval_ms: int = 500,
    max_batch_size: int = 30,
) -> FastAPI:
    project_root = project_root.resolve()
    runs_root = project_root / "agent_runtime" / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    probe_config = build_probe_config(
        instance_id, probe_token, flush_interval_ms, max_batch_size
    )
    probe_script = load_probe_script()

    app = FastAPI(title="Agent Runtime Probe Runner")
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        return error_response(
            message=str(exc.detail), status_code=exc.status_code, code=exc.status_code
        )

    @app.middleware("http")
    async def inject_runtime_probe(request: Request, call_next):
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")
        if (
            request.method == "GET"
            and response.status_code == 200
            and "text/html" in content_type
            and not request.url.path.startswith("/__probe__/")
        ):
            body = b""
            if getattr(response, "body_iterator", None) is not None:
                async for chunk in response.body_iterator:
                    body += chunk
            else:
                body = getattr(response, "body", b"")
            headers = dict(response.headers)
            headers.pop("content-length", None)
            response = HTMLResponse(
                content=inject_probe_assets(body.decode("utf-8"), probe_config),
                status_code=response.status_code,
                headers=headers,
            )

        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.get("/__probe__/health")
    def probe_health() -> JSONResponse:
        return success_response(
            {
                "ok": True,
                "instanceId": instance_id,
            }
        )

    @app.get("/__probe__/probe.js")
    def serve_probe_js() -> Response:
        return Response(content=probe_script, media_type="application/javascript")

    @app.post("/__probe__/collect")
    async def collect_events(request: Request) -> JSONResponse:
        payload = parse_payload(await request.body())
        run_id, _ = ensure_instance(
            payload, instance_id=instance_id, probe_token=probe_token
        )
        meta_update = normalize_meta(
            payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        )
        page_id = str(payload.get("pageId") or payload.get("page_id") or "").strip()
        navigation_id = str(
            payload.get("navigationId") or payload.get("navigation_id") or ""
        ).strip()
        events = payload.get("events") or []
        run_dir = runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        if is_finalized(run_dir):
            total_events = int(
                ensure_json(run_dir / "meta.json", {}).get("total_events", 0)
            )
            return success_response(
                {
                    "accepted": True,
                    "ignored": True,
                    "alreadyFinalized": True,
                    "batchEvents": 0,
                    "totalEvents": total_events,
                }
            )
        accepted_count, total_events = append_events(
            run_dir,
            run_id,
            events,
            page_id=page_id,
            navigation_id=navigation_id,
            meta_update=meta_update,
        )
        return success_response(
            {
                "accepted": True,
                "batchEvents": accepted_count,
                "totalEvents": total_events,
            }
        )

    @app.post("/__probe__/finalize")
    async def finalize_run(request: Request) -> JSONResponse:
        payload = parse_payload(await request.body())
        run_id, _ = ensure_instance(
            payload, instance_id=instance_id, probe_token=probe_token
        )
        meta_update = normalize_meta(
            payload.pop("meta", {}) if isinstance(payload.get("meta"), dict) else {}
        )
        page_id = str(payload.get("pageId") or payload.get("page_id") or "").strip()
        navigation_id = str(
            payload.get("navigationId") or payload.get("navigation_id") or ""
        ).strip()
        events = payload.pop("events", []) or []
        run_dir = runs_root / run_id
        with run_lock_for(run_id):
            run_dir.mkdir(parents=True, exist_ok=True)
            if is_finalized(run_dir):
                compile_result = ensure_json(run_dir / "compile_result.json", {})
                replay_result = ensure_json(run_dir / "replay_result.json", {})
                return success_response(
                    {
                        "accepted": True,
                        "alreadyFinalized": True,
                        "compileTriggered": bool(compile_result),
                        "replayTriggered": bool(replay_result),
                    }
                )
            append_events(
                run_dir,
                run_id,
                events,
                page_id=page_id,
                navigation_id=navigation_id,
                meta_update=meta_update,
            )
            finalize_payload = normalize_finalize_payload(payload)
            compile_result, replay_result = write_finalize(
                project_root=project_root,
                run_dir=run_dir,
                run_id=run_id,
                payload=finalize_payload,
                meta_update=meta_update,
            )
        return success_response(
            {
                "accepted": True,
                "compileTriggered": bool(compile_result),
                "replayTriggered": bool(replay_result),
                "compileResult": compile_result,
                "replayResult": replay_result,
            }
        )

    @app.post("/__probe__/close")
    async def close_run(request: Request) -> JSONResponse:
        payload = parse_payload(await request.body())
        run_id, _ = ensure_instance(
            payload, instance_id=instance_id, probe_token=probe_token
        )
        meta_update = normalize_meta(
            payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        )
        page_id = str(payload.get("pageId") or payload.get("page_id") or "").strip()
        navigation_id = str(
            payload.get("navigationId") or payload.get("navigation_id") or ""
        ).strip()
        run_dir = runs_root / run_id
        with run_lock_for(run_id):
            run_dir.mkdir(parents=True, exist_ok=True)
            if is_finalized(run_dir):
                compile_result = ensure_json(run_dir / "compile_result.json", {})
                replay_result = ensure_json(run_dir / "replay_result.json", {})
                return success_response(
                    {
                        "accepted": True,
                        "ignored": True,
                        "alreadyFinalized": True,
                        "forcedFinalize": False,
                        "compileTriggered": bool(compile_result),
                        "replayTriggered": bool(replay_result),
                    }
                )
            append_events(
                run_dir,
                run_id,
                payload.get("events") or [],
                page_id=page_id,
                navigation_id=navigation_id,
                meta_update=meta_update,
            )
            raw_finalize = payload.get("finalize")
            finalize_input: dict[str, Any] = (
                raw_finalize if isinstance(raw_finalize, dict) else {}
            )
            finalize_payload = normalize_finalize_payload(finalize_input)
            close_reason = str(
                payload.get("reason")
                or finalize_payload.get("done_reason")
                or "context_close"
            )
            finalize_payload.setdefault("done", False)
            finalize_payload.setdefault("done_reason", close_reason)
            finalize_payload.setdefault("force_finalize", True)
            finalize_payload.setdefault("finalize_source", "context_close")
            finalize_payload.setdefault("run_end_reason", close_reason)
            finalize_payload.setdefault("page_type", meta_update.get("page_type"))
            finalize_payload.setdefault("entry_path", meta_update.get("entry_path"))
            compile_result, replay_result = write_finalize(
                project_root=project_root,
                run_dir=run_dir,
                run_id=run_id,
                payload=finalize_payload,
                meta_update=meta_update,
            )
        return success_response(
            {
                "accepted": True,
                "forcedFinalize": True,
                "compileTriggered": bool(compile_result),
                "replayTriggered": bool(replay_result),
                "compileResult": compile_result,
                "replayResult": replay_result,
            }
        )

    app.mount(
        "/", SafeStaticFiles(directory=str(project_root), html=True), name="static-root"
    )
    return app


def main(default_project_root: Path | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Serve the unified __probe__ runtime protocol."
    )
    parser.add_argument(
        "--project-root", type=Path, default=default_project_root or Path.cwd()
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--instance-id", default=os.environ.get("OBSERVABLE_INSTANCE_ID", "rt_demo")
    )
    parser.add_argument(
        "--probe-token",
        default=os.environ.get("OBSERVABLE_PROBE_TOKEN", "probe_tk_demo"),
    )
    parser.add_argument("--flush-interval-ms", type=int, default=500)
    parser.add_argument("--max-batch-size", type=int, default=30)
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(
        create_app(
            args.project_root.resolve(),
            instance_id=args.instance_id,
            probe_token=args.probe_token,
            flush_interval_ms=args.flush_interval_ms,
            max_batch_size=args.max_batch_size,
        ),
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
