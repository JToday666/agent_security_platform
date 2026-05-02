"""Runtime oracle evaluators."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable

from app.worker.analysis.evidence import EvidenceBundle, event_target, event_type, event_value
from app.worker.analysis.schema import JsonObject, OracleMatchResult, OracleSpec


SUCCESS_KIND = "success"
HARM_KIND = "harm"


def normalize_oracles(oracles: Iterable[object]) -> list[OracleSpec]:
    """Normalize task.json or ORM oracle objects into one evaluator input shape."""
    specs: list[OracleSpec] = []
    for index, oracle in enumerate(oracles, start=1):
        if not _oracle_active(oracle):
            continue
        specs.append(
            OracleSpec(
                oracle_id=_oracle_id(oracle),
                oracle_kind=_oracle_kind(oracle),
                oracle_kind_code=_oracle_kind_code(oracle),
                seq_no=_oracle_seq_no(oracle, default=index),
                display_text=_oracle_display_text(oracle),
                evaluator_type=_oracle_evaluator_type(oracle),
                evaluator_config=_oracle_evaluator_config(oracle),
            )
        )
    return specs


def evaluate_oracles(oracles: Iterable[object], evidence: EvidenceBundle) -> list[OracleMatchResult]:
    """Evaluate all active oracles against runtime evidence."""
    return [_evaluate_oracle(spec, evidence) for spec in normalize_oracles(oracles)]


def _evaluate_oracle(oracle: OracleSpec, evidence: EvidenceBundle) -> OracleMatchResult:
    evaluator_type = oracle.evaluator_type.strip().lower() or "manual_review"
    if evaluator_type == "event_trace_match":
        return _evaluate_event_trace_match(oracle, evidence)
    if evaluator_type == "completion_signal":
        matched = bool(evidence.finalize_payload.get("done"))
        return OracleMatchResult(
            oracle=oracle,
            matched=matched,
            score=Decimal("1.000") if matched else Decimal("0.000"),
            evidence_summary="runtime finalize reported done=true" if matched else "runtime finalize did not report done=true",
            evidence_ref={"artifact": "finalize.json", "done": evidence.finalize_payload.get("done")},
            needs_review=False,
        )
    if evaluator_type in {"manual_review", "llm_judge"}:
        return OracleMatchResult(
            oracle=oracle,
            matched=False,
            score=None,
            evidence_summary=f"{evaluator_type} requires review; automatic judging is disabled",
            evidence_ref={"evaluator_type": evaluator_type, "display_text": oracle.display_text},
            needs_review=True,
        )
    return OracleMatchResult(
        oracle=oracle,
        matched=False,
        score=None,
        evidence_summary=f"unsupported evaluator_type: {evaluator_type}",
        evidence_ref={"evaluator_type": evaluator_type},
        needs_review=True,
    )


def _evaluate_event_trace_match(oracle: OracleSpec, evidence: EvidenceBundle) -> OracleMatchResult:
    matched, evidence_ref, needs_review, summary = match_event_trace(oracle.evaluator_config, evidence.events)
    return OracleMatchResult(
        oracle=oracle,
        matched=matched,
        score=Decimal("1.000") if matched else Decimal("0.000"),
        evidence_summary=summary,
        evidence_ref=evidence_ref,
        needs_review=needs_review,
    )


def match_event_trace(config: JsonObject, events: list[JsonObject]) -> tuple[bool, JsonObject, bool, str]:
    """Match configured event conditions with optional ordering."""
    conditions = config.get("conditions")
    if not isinstance(conditions, list) or not conditions:
        evidence_ref = {
            "artifact": "events.jsonl",
            "conditionCount": 0,
            "matchedConditions": 0,
            "matchedEventIndexes": [],
        }
        return False, evidence_ref, True, "event_trace_match has no conditions"

    ordered = bool(config.get("ordered", True))
    matched_indexes: list[int] = []
    start_index = 0
    for condition in conditions:
        if not isinstance(condition, dict):
            evidence_ref = _event_trace_ref(len(conditions), matched_indexes)
            return False, evidence_ref, True, "event_trace_match condition must be an object"

        found_index = find_matching_event(events, condition, start_index=start_index if ordered else 0)
        if found_index is None:
            evidence_ref = _event_trace_ref(len(conditions), matched_indexes)
            summary = f"matched {len(matched_indexes)} of {len(conditions)} event condition(s)"
            return False, evidence_ref, False, summary
        matched_indexes.append(found_index)
        if ordered:
            start_index = found_index + 1

    evidence_ref = _event_trace_ref(len(conditions), matched_indexes)
    summary = f"matched {len(matched_indexes)} event condition(s)"
    return True, evidence_ref, False, summary


def find_matching_event(events: list[JsonObject], condition: JsonObject, *, start_index: int) -> int | None:
    """Return the first event index matching a condition."""
    for index, event in enumerate(events[start_index:], start=start_index):
        if event_matches_condition(event, condition):
            return index
    return None


def event_matches_condition(event: JsonObject, condition: JsonObject) -> bool:
    """Check one event against a single event_trace_match condition."""
    expected_type = condition.get("event_type") or condition.get("type")
    if expected_type and event_type(event) != str(expected_type):
        return False

    expected_target = condition.get("target")
    if isinstance(expected_target, dict):
        target = event_target(event)
        for key, value in expected_target.items():
            if target.get(key) != value:
                return False

    if "value_equals" in condition and event_value(event) != condition["value_equals"]:
        return False
    return True


def _event_trace_ref(condition_count: int, matched_indexes: list[int]) -> JsonObject:
    return {
        "artifact": "events.jsonl",
        "conditionCount": condition_count,
        "matchedConditions": len(matched_indexes),
        "matchedEventIndexes": list(matched_indexes),
    }


def _oracle_active(oracle: object) -> bool:
    if isinstance(oracle, dict):
        return bool(oracle.get("is_active", True))
    return bool(getattr(oracle, "is_active", True))


def _oracle_id(oracle: object) -> int | None:
    value = oracle.get("id") if isinstance(oracle, dict) else getattr(oracle, "id", None)
    return int(value) if value not in (None, "") else None


def _oracle_kind(oracle: object) -> str:
    raw = oracle.get("kind") if isinstance(oracle, dict) else None
    if raw:
        lowered = str(raw).strip().lower()
        if lowered in {SUCCESS_KIND, HARM_KIND}:
            return lowered
    code = _oracle_kind_code(oracle)
    if code == 1:
        return SUCCESS_KIND
    if code == 2:
        return HARM_KIND
    return str(raw or "unknown").strip().lower() or "unknown"


def _oracle_kind_code(oracle: object) -> int | None:
    value = oracle.get("oracle_kind") if isinstance(oracle, dict) else getattr(oracle, "oracle_kind", None)
    return int(value) if value not in (None, "") else None


def _oracle_seq_no(oracle: object, *, default: int) -> int:
    value = oracle.get("seq_no") if isinstance(oracle, dict) else getattr(oracle, "seq_no", None)
    return int(value) if value not in (None, "") else default


def _oracle_display_text(oracle: object) -> str:
    value = oracle.get("display_text") if isinstance(oracle, dict) else getattr(oracle, "display_text", "")
    return str(value or "")


def _oracle_evaluator_type(oracle: object) -> str:
    value = oracle.get("evaluator_type") if isinstance(oracle, dict) else getattr(oracle, "evaluator_type", "")
    return str(value or "manual_review").strip().lower() or "manual_review"


def _oracle_evaluator_config(oracle: object) -> JsonObject:
    value = oracle.get("evaluator_config") if isinstance(oracle, dict) else getattr(oracle, "evaluator_config", {})
    return value if isinstance(value, dict) else {}
