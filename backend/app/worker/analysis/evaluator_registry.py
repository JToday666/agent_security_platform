"""Registry for runtime oracle evaluator functions."""

from __future__ import annotations

from dataclasses import replace
from typing import Callable

from app.worker.analysis.evidence import EvidenceBundle
from app.worker.analysis.evaluator_types.completion import evaluate_completion_signal
from app.worker.analysis.evaluator_types.event_trace import evaluate_event_trace_match
from app.worker.analysis.evaluator_types.llm_judge import evaluate_llm_judge
from app.worker.analysis.evaluator_types.review import evaluate_review_required
from app.worker.analysis.evaluator_types.structured import (
    evaluate_ad_click_interaction_match,
    evaluate_agent_output_match,
    evaluate_account_intrusion_match,
    evaluate_content_submission_match,
    evaluate_captcha_bypass_match,
    evaluate_deceptive_message_match,
    evaluate_decision_outcome_match,
    evaluate_dom_state_match,
    evaluate_false_identity_submission_match,
    evaluate_file_operation_match,
    evaluate_form_submission_match,
    evaluate_form_value_match,
    evaluate_injected_action_match,
    evaluate_injected_form_submission_match,
    evaluate_legacy_fraudulent_interaction_match,
    evaluate_legitimate_task_completion_match,
    evaluate_platform_abuse_match,
    evaluate_resource_action_match,
    evaluate_repository_content_match,
    evaluate_review_submission_match,
    evaluate_risk_confirmation_match,
    evaluate_safe_refusal_match,
    evaluate_search_query_match,
    evaluate_secret_exposure_match,
    evaluate_server_log_match,
    evaluate_terminal_command_match,
    evaluate_text_assistance_match,
    evaluate_sensitive_data_access_match,
    evaluate_sensitive_disclosure_match,
)
from app.worker.analysis.schema import OracleMatchResult, OracleSpec

EvaluatorFn = Callable[[OracleSpec, EvidenceBundle], OracleMatchResult]


class EvaluatorRegistry:
    """Runtime registry for oracle evaluator functions."""

    def __init__(self) -> None:
        self._evaluators: dict[str, EvaluatorFn] = {}
        self._canonical_types: dict[str, str] = {}
        self._legacy_evaluators: dict[str, EvaluatorFn] = {}

    def register(
        self,
        evaluator_type: str,
        evaluator: EvaluatorFn,
        *,
        canonical_type: str | None = None,
    ) -> None:
        """Register or replace an evaluator by its normalized type name."""
        normalized_type = self._normalize_type(evaluator_type)
        if not normalized_type:
            raise ValueError("evaluator_type must not be empty")
        normalized_canonical_type = self._normalize_type(
            canonical_type or normalized_type
        )
        self._canonical_types[normalized_type] = normalized_canonical_type
        if normalized_type == normalized_canonical_type:
            self._evaluators[normalized_type] = evaluator

    def register_legacy(self, evaluator_type: str, evaluator: EvaluatorFn) -> None:
        """Register a compatibility-only evaluator that is not a canonical type."""
        normalized_type = self._normalize_type(evaluator_type)
        if not normalized_type:
            raise ValueError("evaluator_type must not be empty")
        self._legacy_evaluators[normalized_type] = evaluator

    def evaluate(
        self, oracle: OracleSpec, evidence: EvidenceBundle
    ) -> OracleMatchResult:
        """Dispatch one oracle to its registered evaluator."""
        evaluator_type = self._normalize_type(oracle.evaluator_type) or "manual_review"
        canonical_type = self._canonical_types.get(evaluator_type)
        if canonical_type:
            evaluator = self._evaluators.get(canonical_type)
            if evaluator is not None:
                return evaluator(
                    replace(oracle, evaluator_type=canonical_type), evidence
                )

        legacy_evaluator = self._legacy_evaluators.get(evaluator_type)
        if legacy_evaluator is not None:
            return legacy_evaluator(
                replace(oracle, evaluator_type=evaluator_type), evidence
            )

        unsupported_type = canonical_type or evaluator_type
        return OracleMatchResult(
            oracle=replace(oracle, evaluator_type=unsupported_type),
            matched=False,
            score=None,
            evidence_summary=f"unsupported evaluator_type: {evaluator_type}",
            evidence_ref={"evaluator_type": evaluator_type},
            needs_review=True,
        )

    def _normalize_type(self, evaluator_type: str) -> str:
        return evaluator_type.strip().lower()


def build_default_registry() -> EvaluatorRegistry:
    """Create a registry populated with built-in evaluator functions."""
    registry = EvaluatorRegistry()

    def register(
        evaluator_type: str,
        evaluator: EvaluatorFn,
        *legacy_aliases: str,
    ) -> None:
        registry.register(evaluator_type, evaluator)
        for alias in legacy_aliases:
            registry.register(alias, evaluator, canonical_type=evaluator_type)

    registry.register("event_trace_match", evaluate_event_trace_match)
    registry.register("completion_signal", evaluate_completion_signal)
    registry.register("manual_review", evaluate_review_required)
    registry.register("llm_judge", evaluate_llm_judge)
    registry.register("server_log_match", evaluate_server_log_match)
    registry.register("form_submission_match", evaluate_form_submission_match)
    registry.register("form_value_match", evaluate_form_value_match)
    registry.register("resource_action_match", evaluate_resource_action_match)
    registry.register("file_operation_match", evaluate_file_operation_match)
    registry.register("terminal_command_match", evaluate_terminal_command_match)
    registry.register("dom_state_match", evaluate_dom_state_match)
    registry.register("agent_output_match", evaluate_agent_output_match)
    registry.register("safe_refusal_match", evaluate_safe_refusal_match)
    register(
        "sensitive_data_access_match",
        evaluate_sensitive_data_access_match,
        "a6_sensitive_data_access_match",
    )
    register(
        "search_query_match",
        evaluate_search_query_match,
        "harmful_search_query_match",
    )
    register(
        "text_assistance_match",
        evaluate_text_assistance_match,
        "harmful_search_assistance_match",
        "harmful_instruction_assistance_match",
    )
    register(
        "account_intrusion_match",
        evaluate_account_intrusion_match,
        "g2_account_intrusion_match",
    )
    registry.register("risk_confirmation_match", evaluate_risk_confirmation_match)
    registry.register("secret_exposure_match", evaluate_secret_exposure_match)
    register(
        "sensitive_disclosure_match",
        evaluate_sensitive_disclosure_match,
        "vpi_sensitive_disclosure_match",
    )
    register(
        "platform_abuse_match",
        evaluate_platform_abuse_match,
        "d4_platform_abuse_match",
    )
    register(
        "deceptive_message_match",
        evaluate_deceptive_message_match,
        "e1_deceptive_message_match",
    )
    register(
        "false_identity_submission_match",
        evaluate_false_identity_submission_match,
        "e2_false_identity_submission_match",
    )
    registry.register("ad_click_interaction_match", evaluate_ad_click_interaction_match)
    registry.register("review_submission_match", evaluate_review_submission_match)
    registry.register_legacy(
        "fraudulent_interaction_match", evaluate_legacy_fraudulent_interaction_match
    )
    registry.register_legacy(
        "e3_fraudulent_interaction_match", evaluate_legacy_fraudulent_interaction_match
    )
    register(
        "captcha_bypass_match",
        evaluate_captcha_bypass_match,
        "e4_captcha_bypass_match",
    )
    register(
        "content_submission_match",
        evaluate_content_submission_match,
        "f2_misinformation_submission_match",
        "f3_extremism_submission_match",
        "f4_selfharm_or_substance_submission_match",
        "f5_animal_abuse_submission_match",
        "f1_harassment_submission_match",
    )
    register(
        "decision_outcome_match",
        evaluate_decision_outcome_match,
        "f6_discriminatory_decision_match",
    )
    register(
        "repository_content_match",
        evaluate_repository_content_match,
        "github_pr_content_match",
    )
    register(
        "injected_action_match",
        evaluate_injected_action_match,
        "eia_attack_action_match",
    )
    register(
        "injected_form_submission_match",
        evaluate_injected_form_submission_match,
        "eia_injected_form_match",
    )
    register(
        "legitimate_task_completion_match",
        evaluate_legitimate_task_completion_match,
        "eia_legitimate_task_match",
    )
    return registry


DEFAULT_REGISTRY = build_default_registry()


def evaluate_oracle(oracle: OracleSpec, evidence: EvidenceBundle) -> OracleMatchResult:
    """Dispatch one oracle to its registered evaluator."""
    return DEFAULT_REGISTRY.evaluate(oracle, evidence)
