"""Event-trace evaluator."""

from __future__ import annotations

from decimal import Decimal

from app.worker.analysis.evidence import EvidenceBundle, event_target, event_type, event_value
from app.worker.analysis.schema import JsonObject, OracleMatchResult, OracleSpec


def evaluate_event_trace_match(oracle: OracleSpec, evidence: EvidenceBundle) -> OracleMatchResult:
    """Evaluate an oracle by matching configured runtime events."""
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
