"""SSRF-oriented URL checks for outbound Agent calls."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.shared.config import settings


class AgentUrlSecurityError(ValueError):
    """Raised when an Agent URL violates outbound request policy."""


def _is_forbidden_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return any(
        [
            ip.is_loopback,
            ip.is_private,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        ]
    )


def validate_agent_base_url(url: str) -> str:
    """Validate and normalize a user supplied Agent base URL."""
    normalized = (url or "").strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise AgentUrlSecurityError("Agent baseUrl 只允许 http 或 https。")

    if settings.AGENT_HTTP_ALLOW_PRIVATE_NETWORKS:
        return normalized

    hostname = parsed.hostname
    try:
        if _is_forbidden_ip(hostname):
            raise AgentUrlSecurityError("Agent baseUrl 不允许指向本机或内网地址。")
    except ValueError:
        pass

    lowered = hostname.lower()
    if lowered in {"localhost", "localhost.localdomain"} or lowered.endswith(".localhost"):
        raise AgentUrlSecurityError("Agent baseUrl 不允许指向本机或内网地址。")

    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return normalized

    for info in infos:
        resolved_ip = info[4][0]
        if _is_forbidden_ip(resolved_ip):
            raise AgentUrlSecurityError("Agent baseUrl 不允许解析到本机或内网地址。")
    return normalized
