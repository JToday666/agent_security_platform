from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from app.worker.analysis.evaluator_types.llm_judge import (
    LLMJudgeConfigError,
    resolve_llm_judge_config,
)
from app.worker.analysis.evaluator_types import llm_judge


@contextmanager
def patched_judge_settings(**overrides: object):
    values = {
        "LLM_JUDGE_PROVIDER": "litellm",
        "LLM_JUDGE_BASE_URL": None,
        "LLM_JUDGE_MODEL": None,
        "LLM_JUDGE_API_KEY": None,
        "LLM_BASE_URL": None,
        "LLM_DEFAULT_MODEL": None,
        "LLM_API_KEY": None,
    }
    values.update(overrides)
    patchers = [
        patch.object(llm_judge.settings, name, value, create=True)
        for name, value in values.items()
    ]
    try:
        for patcher in patchers:
            patcher.start()
        yield
    finally:
        for patcher in reversed(patchers):
            patcher.stop()


def test_litellm_judge_provider_uses_global_openai_compatible_settings() -> None:
    with patched_judge_settings(
        LLM_BASE_URL="http://127.0.0.1:18400/v1/",
        LLM_DEFAULT_MODEL="local-qwen",
    ):
        config = resolve_llm_judge_config()

    assert config.provider == "litellm"
    assert config.base_url == "http://127.0.0.1:18400/v1"
    assert config.model == "local-qwen"
    assert config.api_key == "EMPTY"


def test_judge_specific_settings_override_global_llm_settings() -> None:
    with patched_judge_settings(
        LLM_BASE_URL="http://127.0.0.1:18400/v1",
        LLM_DEFAULT_MODEL="local-qwen",
        LLM_API_KEY="global-key",
        LLM_JUDGE_BASE_URL="http://127.0.0.1:18500/v1",
        LLM_JUDGE_MODEL="judge-qwen",
        LLM_JUDGE_API_KEY="judge-key",
    ):
        config = resolve_llm_judge_config()

    assert config.provider == "litellm"
    assert config.base_url == "http://127.0.0.1:18500/v1"
    assert config.model == "judge-qwen"
    assert config.api_key == "judge-key"


def test_openai_compatible_provider_uses_generic_llm_settings() -> None:
    with patched_judge_settings(
        LLM_JUDGE_PROVIDER="openai-compatible",
        LLM_BASE_URL="http://127.0.0.1:18400/v1",
        LLM_DEFAULT_MODEL="local-qwen",
    ):
        config = resolve_llm_judge_config()

    assert config.provider == "openai-compatible"
    assert config.base_url == "http://127.0.0.1:18400/v1"
    assert config.model == "local-qwen"
    assert config.api_key == "EMPTY"


def test_provider_preset_can_use_global_llm_api_key() -> None:
    with patched_judge_settings(
        LLM_JUDGE_PROVIDER="deepseek",
        LLM_API_KEY="global-key",
    ):
        config = resolve_llm_judge_config()

    assert config.provider == "deepseek"
    assert config.base_url == "https://api.deepseek.com"
    assert config.model == "deepseek-chat"
    assert config.api_key == "global-key"


def test_generic_provider_requires_base_url_and_model() -> None:
    with patched_judge_settings(LLM_JUDGE_PROVIDER="custom"):
        with pytest.raises(LLMJudgeConfigError, match="LLM_JUDGE_MODEL"):
            resolve_llm_judge_config()


def test_unsupported_provider_reports_supported_values() -> None:
    with patched_judge_settings(LLM_JUDGE_PROVIDER="unsupported"):
        with pytest.raises(LLMJudgeConfigError, match="supported:"):
            resolve_llm_judge_config()
