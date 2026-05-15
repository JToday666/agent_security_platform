"""Identifier helpers for registered Agents."""

from uuid import uuid4


def generate_agent_id() -> str:
    """Generate a public Agent identifier."""
    return f"agt_{uuid4().hex[:12]}"
