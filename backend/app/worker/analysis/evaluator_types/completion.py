"""Completion-signal evaluator."""

from __future__ import annotations

from decimal import Decimal

from app.worker.analysis.evidence import EvidenceBundle
from app.worker.analysis.schema import OracleMatchResult, OracleSpec


def evaluate_completion_signal(
    oracle: OracleSpec, evidence: EvidenceBundle
) -> OracleMatchResult:
    """Evaluate completion from runtime finalize payload."""
    done = bool(evidence.finalize_payload.get("done"))
    allowed_signals = _configured_signals(oracle.evaluator_config)
    observed_signals = _observed_signals(evidence.finalize_payload)
    signal_matched = not allowed_signals or bool(allowed_signals & observed_signals)
    matched = done and signal_matched
    return OracleMatchResult(
        oracle=oracle,
        matched=matched,
        score=Decimal("1.000") if matched else Decimal("0.000"),
        evidence_summary=(
            "runtime finalize reported done=true"
            if matched
            else "runtime finalize did not match required completion signal"
            if done and allowed_signals
            else "runtime finalize did not report done=true"
        ),
        evidence_ref={
            "artifact": "finalize.json",
            "done": evidence.finalize_payload.get("done"),
            "allowedSignals": sorted(allowed_signals),
            "observedSignals": sorted(observed_signals),
        },
        needs_review=False,
    )


def _configured_signals(config: dict[str, object]) -> set[str]:
    raw = config.get("completion_signals") or config.get("done_reasons")
    if isinstance(raw, str):
        values = [raw]
    elif isinstance(raw, list):
        values = raw
    else:
        values = []
    return {str(value).strip().lower() for value in values if str(value).strip()}


def _observed_signals(finalize_payload: dict[str, object]) -> set[str]:
    signals: set[str] = set()
    for key in ("done_reason", "run_end_reason", "completion_signal"):
        value = finalize_payload.get(key)
        if value not in (None, ""):
            signals.add(str(value).strip().lower())
    final_state = finalize_payload.get("final_state")
    if isinstance(final_state, dict):
        for key in ("completion_signal", "done_reason", "run_end_reason"):
            value = final_state.get(key)
            if value not in (None, ""):
                signals.add(str(value).strip().lower())
    return signals
