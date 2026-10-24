"""Bounded request-body reading for http.server handlers (stdlib only, copy into your project).

Reading `rfile.read(n)` with an attacker-chosen `n` lets one request claim as much memory as it likes
(CWE-770; OWASP API4:2023 asks for a maximum size on every incoming input). This helper refuses before reading.
Chunked bodies are refused because http.server does not decode them, so the declared length is the only bound.
This does not bound how long a client may stall after sending the header: set `timeout` on the handler class
(BaseHTTPRequestHandler.timeout is None by default) and serve with ThreadingHTTPServer.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler


def read_limited_body(handler: BaseHTTPRequestHandler, max_request_bytes: int) -> bytes | None:
    """Return the request body, or send 400/411/413 and return None when its declared length is not acceptable."""
    if handler.headers.get("Transfer-Encoding"):
        handler.send_error(411, "Content-Length is required; chunked bodies are not accepted")
        return None
    declared = handler.headers.get("Content-Length")
    if declared is None:
        handler.send_error(411, "Content-Length is required")
        return None
    if not (declared.isascii() and declared.isdigit()):  # int() would also accept "+5", " 5", "1_0"; a proxy may read those differently
        handler.send_error(400, "Content-Length must be a plain decimal number")
        return None
    length = int(declared)
    if length > max_request_bytes:
        handler.send_error(413, "Request body too large")
        return None
    return handler.rfile.read(length)
