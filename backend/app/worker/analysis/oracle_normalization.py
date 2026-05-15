"""Normalize oracle definitions for runtime evaluators."""

from __future__ import annotations

from typing import Iterable

from app.worker.analysis.schema import JsonObject, OracleSpec

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


def _oracle_active(oracle: object) -> bool:
    if isinstance(oracle, dict):
        return bool(oracle.get("is_active", True))
    return bool(getattr(oracle, "is_active", True))


def _oracle_id(oracle: object) -> int | None:
    value = (
        oracle.get("id") if isinstance(oracle, dict) else getattr(oracle, "id", None)
    )
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
    value = (
        oracle.get("oracle_kind")
        if isinstance(oracle, dict)
        else getattr(oracle, "oracle_kind", None)
    )
    return int(value) if value not in (None, "") else None


def _oracle_seq_no(oracle: object, *, default: int) -> int:
    value = (
        oracle.get("seq_no")
        if isinstance(oracle, dict)
        else getattr(oracle, "seq_no", None)
    )
    return int(value) if value not in (None, "") else default


def _oracle_display_text(oracle: object) -> str:
    value = (
        oracle.get("display_text")
        if isinstance(oracle, dict)
        else getattr(oracle, "display_text", "")
    )
    return str(value or "")


def _oracle_evaluator_type(oracle: object) -> str:
    value = (
        oracle.get("evaluator_type")
        if isinstance(oracle, dict)
        else getattr(oracle, "evaluator_type", "")
    )
    return str(value or "manual_review").strip().lower() or "manual_review"


def _oracle_evaluator_config(oracle: object) -> JsonObject:
    value = (
        oracle.get("evaluator_config")
        if isinstance(oracle, dict)
        else getattr(oracle, "evaluator_config", {})
    )
    return value if isinstance(value, dict) else {}
