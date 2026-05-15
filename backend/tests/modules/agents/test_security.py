from __future__ import annotations

import pytest

from app.modules.agents.security import AgentUrlSecurityError, validate_agent_base_url


def test_validate_agent_base_url_rejects_localhost_and_private_hosts() -> None:
    for url in [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://10.0.0.5",
        "http://172.16.0.5",
        "http://192.168.1.20",
    ]:
        with pytest.raises(AgentUrlSecurityError):
            validate_agent_base_url(url)


def test_validate_agent_base_url_allows_public_http_hosts() -> None:
    assert (
        validate_agent_base_url("https://api.agent.example.com")
        == "https://api.agent.example.com"
    )
