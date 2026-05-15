"""Compatibility facade for runtime oracle evaluators."""

from __future__ import annotations

from typing import Iterable

from app.worker.analysis.evidence import EvidenceBundle
from app.worker.analysis.evaluator_registry import evaluate_oracle
from app.worker.analysis.evaluator_types.event_trace import (
    event_matches_condition,
    find_matching_event,
    match_event_trace,
)
from app.worker.analysis.oracle_normalization import (
    HARM_KIND,
    SUCCESS_KIND,
    normalize_oracles,
)
from app.worker.analysis.schema import OracleMatchResult


def evaluate_oracles(
    oracles: Iterable[object], evidence: EvidenceBundle
) -> list[OracleMatchResult]:
    """Evaluate all active oracles against runtime evidence."""
    return [evaluate_oracle(spec, evidence) for spec in normalize_oracles(oracles)]


__all__ = [
    "HARM_KIND",
    "SUCCESS_KIND",
    "evaluate_oracles",
    "normalize_oracles",
    "match_event_trace",
    "find_matching_event",
    "event_matches_condition",
]
