from __future__ import annotations

from unittest.mock import patch

from app.worker.analysis.evaluator_types.llm_judge import resolve_llm_judge_config
from app.worker.analysis.evaluator_types import llm_judge


def test_vllm_judge_provider_uses_local_openai_compatible_settings() -> None:
    with (
        patch.object(llm_judge.settings, "LLM_JUDGE_PROVIDER", "vllm"),
        patch.object(llm_judge.settings, "LLM_JUDGE_BASE_URL", None),
        patch.object(llm_judge.settings, "LLM_JUDGE_MODEL", None),
        patch.object(llm_judge.settings, "LLM_JUDGE_API_KEY", None),
        patch.object(llm_judge.settings, "VLLM_BASE_URL", "http://127.0.0.1:18000/v1"),
        patch.object(llm_judge.settings, "VLLM_MODEL", "qwen2.5-14b-gptq-int4"),
    ):
        config = resolve_llm_judge_config()

    assert config.provider == "vllm"
    assert config.base_url == "http://127.0.0.1:18000/v1"
    assert config.model == "qwen2.5-14b-gptq-int4"
    assert config.api_key == "EMPTY"
