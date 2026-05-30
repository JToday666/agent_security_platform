"""Build Evidence IR from runtime artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.worker.analysis.schema import EvidenceItem, JsonObject


@dataclass(slots=True)
class EvidenceBundle:
    """Normalized runtime evidence consumed by evaluators."""

    events: list[JsonObject]
    finalize_payload: JsonObject
    meta_payload: JsonObject
    runtime_context_payload: JsonObject
    server_logs: list[JsonObject]
    evidence: list[EvidenceItem]
    warnings: list[str]
    errors: list[str]
    task_payload: JsonObject | None = None


def build_evidence_bundle(
    run_dir: Path, *, task_payload: JsonObject | None = None
) -> EvidenceBundle:
    """Load runtime artifacts and convert them into evaluator-friendly evidence."""
    warnings: list[str] = []
    errors: list[str] = []
    events = _load_events(run_dir / "events.jsonl", warnings=warnings, errors=errors)
    finalize_payload = _load_json(
        run_dir / "finalize.json", warnings=warnings, errors=errors, required=True
    )
    meta_payload = _load_json(
        run_dir / "meta.json", warnings=warnings, errors=errors, required=False
    )
    runtime_context_payload = _load_json(
        run_dir / "runtime_context.json",
        warnings=warnings,
        errors=errors,
        required=False,
    )
    server_logs = _load_fresh_server_logs(run_dir, warnings=warnings, errors=errors)
    evidence = [
        _event_to_evidence_item(index, event) for index, event in enumerate(events)
    ]
    evidence.extend(
        _server_log_to_evidence_item(index, record)
        for index, record in enumerate(server_logs)
    )
    if finalize_payload:
        evidence.append(
            EvidenceItem(
                source="finalize.json",
                summary=f"finalize done={bool(finalize_payload.get('done'))}",
                value=finalize_payload.get("done"),
            )
        )
    return EvidenceBundle(
        events=events,
        finalize_payload=finalize_payload,
        meta_payload=meta_payload,
        runtime_context_payload=runtime_context_payload,
        server_logs=server_logs,
        evidence=evidence,
        warnings=warnings,
        errors=errors,
        task_payload=task_payload,
    )


def event_type(event: JsonObject) -> str:
    """Return a stable event type from common runtime field variants."""
    return str(
        event.get("type") or event.get("event_type") or event.get("eventType") or ""
    )


def event_target(event: JsonObject) -> JsonObject:
    """Return target metadata for an event."""
    target = event.get("target")
    return target if isinstance(target, dict) else {}


def event_value(event: JsonObject) -> Any:
    """Extract the most useful event value from normalized runtime event shapes."""
    for key in ("value", "input_value", "inputValue", "text"):
        if key in event:
            return event[key]
    for container_key in ("extra", "payload"):
        container = event.get(container_key)
        if isinstance(container, dict):
            for key in ("value", "input_value", "inputValue", "text"):
                if key in container:
                    return container[key]
    return None


def _event_to_evidence_item(index: int, event: JsonObject) -> EvidenceItem:
    kind = event_type(event) or "unknown"
    target = event_target(event)
    value = event_value(event)
    summary_pieces = [f"event[{index}] type={kind}"]
    if target:
        target_hint = (
            target.get("testId")
            or target.get("id")
            or target.get("name")
            or target.get("selector")
        )
        if target_hint:
            summary_pieces.append(f"target={target_hint}")
    if value not in (None, ""):
        summary_pieces.append("value_observed=true")
    return EvidenceItem(
        source="events.jsonl",
        index=index,
        event_type=kind,
        target=target,
        value=value,
        summary=", ".join(summary_pieces),
    )


def _server_log_to_evidence_item(index: int, record: JsonObject) -> EvidenceItem:
    source = str(record.get("source") or "text_server/saved_logs")
    log_type = str(record.get("log_type") or "unknown")
    count = len(record.get("records") or [])
    return EvidenceItem(
        source=source,
        index=index,
        event_type="server_log",
        value=record.get("records"),
        summary=f"server_log type={log_type}, records={count}",
    )


def _load_events(
    path: Path, *, warnings: list[str], errors: list[str]
) -> list[JsonObject]:
    if not path.exists():
        warnings.append(f"{path.name} not found")
        return []

    events: list[JsonObject] = []
    for line_no, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}:{line_no}: invalid json: {exc.msg}")
            continue
        if isinstance(payload, dict):
            events.append(payload)
        else:
            warnings.append(f"{path.name}:{line_no}: ignored non-object event")
    if not events:
        warnings.append("events.jsonl contains no usable events")
    return events


def _load_json(
    path: Path, *, warnings: list[str], errors: list[str], required: bool
) -> JsonObject:
    if not path.exists():
        message = f"{path.name} not found"
        if required:
            errors.append(message)
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid json: {exc.msg}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"{path.name}: expected JSON object")
        return {}
    return payload


def _load_fresh_server_logs(
    run_dir: Path, *, warnings: list[str], errors: list[str]
) -> list[JsonObject]:
    """Load text_server logs written after the runtime workspace was prepared."""
    try:
        project_root = run_dir.parents[2]
    except IndexError:
        return []
    if not project_root.exists():
        return []

    try:
        min_mtime = run_dir.stat().st_mtime - 1.0
    except OSError:
        min_mtime = 0.0

    records: list[JsonObject] = []
    for path in sorted(project_root.glob("**/text_server/saved_logs/*")):
        if not path.is_file():
            continue
        try:
            if path.stat().st_mtime < min_mtime:
                continue
            parsed = _parse_server_log(path)
        except OSError as exc:
            warnings.append(f"{path.name}: could not read server log: {exc}")
            continue
        except ValueError as exc:
            errors.append(f"{path.name}: invalid server log: {exc}")
            continue
        records.append(parsed)
    return records


def _parse_server_log(path: Path) -> JsonObject:
    text = path.read_text(encoding="utf-8")
    log_type = path.name.split("_behaviorID=", 1)[0]
    if path.suffix.lower() == ".json":
        payload = json.loads(text) if text.strip() else []
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict):
            records = [payload]
        else:
            raise ValueError("expected JSON object or array")
        return {
            "source": path.as_posix(),
            "log_type": log_type,
            "records": [record for record in records if isinstance(record, dict)],
        }

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return {
        "source": path.as_posix(),
        "log_type": log_type,
        "records": [{"text": line} for line in lines],
    }
