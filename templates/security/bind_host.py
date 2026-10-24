"""Loopback-by-default bind address with an explicit, announced opt-in (stdlib only, copy into your project).

Binding to every interface exposes the service to everyone on the network (CWE-1327). This keeps the default on
loopback and lets the operator opt in through an environment variable, with a warning that says what that means.
"""

from __future__ import annotations

import os

LOOPBACK_HOSTS = ("127.0.0.1", "::1", "localhost")


def resolve_host(env_var: str, default: str = "127.0.0.1") -> tuple[str, str | None]:
    """Return (host, warning); `warning` is None while the host stays on loopback."""
    host = os.environ.get(env_var, "").strip() or default
    if host in LOOPBACK_HOSTS:
        return host, None
    return host, (
        f"[주의] {host} 로 열렸습니다. 같은 네트워크의 누구나 접속할 수 있습니다. "
        "인증과 요청 속도 제한이 없다면 공개 인터넷에는 노출하지 마세요."
    )
