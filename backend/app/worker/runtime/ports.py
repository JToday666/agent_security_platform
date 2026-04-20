"""Networking helpers for worker runtime processes."""

from __future__ import annotations

import socket


def allocate_tcp_port(host: str = "127.0.0.1") -> int:
    """Reserve an ephemeral TCP port by probing the OS."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, 0))
        return int(sock.getsockname()[1])
