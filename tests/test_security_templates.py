"""Regression tests for templates/security (drop-in controls the situation matrix points to)."""

from __future__ import annotations

import http.client
import importlib.util
import os
import shutil
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates" / "security"
sys.path.insert(0, str(ROOT / "scripts"))

import check_exposure_hotspots
import check_security_hotspots


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"tpl_{name}", TEMPLATES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


limiter_mod = load("rate_limiter")
limits_mod = load("request_limits")
bind_mod = load("bind_host")


class RateLimiterTests(unittest.TestCase):
    def test_allows_up_to_the_limit_then_blocks(self) -> None:
        limiter = limiter_mod.SlidingWindowLimiter(limit=3, window_seconds=10)
        self.assertEqual([limiter.allow("a", now=1.0) for _ in range(4)], [True, True, True, False])

    def test_window_slides(self) -> None:
        limiter = limiter_mod.SlidingWindowLimiter(limit=1, window_seconds=10)
        self.assertTrue(limiter.allow("a", now=0.0))
        self.assertFalse(limiter.allow("a", now=9.9))
        self.assertTrue(limiter.allow("a", now=10.1))

    def test_keys_are_independent(self) -> None:
        limiter = limiter_mod.SlidingWindowLimiter(limit=1, window_seconds=10)
        self.assertTrue(limiter.allow("1.2.3.4", now=0.0))
        self.assertTrue(limiter.allow("5.6.7.8", now=0.0))
        self.assertFalse(limiter.allow("1.2.3.4", now=1.0))

    def test_key_table_stays_bounded_under_address_rotation(self) -> None:
        limiter = limiter_mod.SlidingWindowLimiter(limit=5, window_seconds=60, max_keys=100)
        for index in range(5000):
            limiter.allow(f"10.0.{index // 250}.{index % 250}", now=float(index) / 1000)
        self.assertLessEqual(len(limiter._events), 100)

    def test_idle_keys_are_forgotten_before_active_ones(self) -> None:
        limiter = limiter_mod.SlidingWindowLimiter(limit=1, window_seconds=10, max_keys=2)
        limiter.allow("old", now=0.0)
        limiter.allow("busy", now=95.0)
        limiter.allow("new", now=100.0)  # table full: "old" is idle (older than the window) and goes first
        self.assertIn("busy", limiter._events)
        self.assertNotIn("old", limiter._events)
        self.assertFalse(limiter.allow("busy", now=100.5))  # busy key kept its history, so it is still limited

    def test_least_recently_seen_key_is_dropped_when_all_are_active(self) -> None:
        limiter = limiter_mod.SlidingWindowLimiter(limit=1, window_seconds=100, max_keys=2)
        limiter.allow("first", now=1.0)
        limiter.allow("second", now=2.0)
        limiter.allow("third", now=3.0)
        self.assertEqual(set(limiter._events), {"second", "third"})

    def test_concurrent_callers_never_exceed_the_limit_or_crash(self) -> None:
        limiter = limiter_mod.SlidingWindowLimiter(limit=50, window_seconds=60, max_keys=20)
        allowed: list[bool] = []
        errors: list[BaseException] = []

        def worker(offset: int) -> None:
            try:
                for index in range(300):
                    key = "shared" if index % 3 == 0 else f"k{offset}-{index}"
                    allowed.append(limiter.allow(key, now=1.0))
            except BaseException as error:  # noqa: BLE001 - the test reports any failure from the shared table
                errors.append(error)

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        self.assertLessEqual(len(limiter._events), 20)

    def test_shared_key_is_limited_exactly_under_concurrency(self) -> None:
        limiter = limiter_mod.SlidingWindowLimiter(limit=25, window_seconds=60)
        results: list[bool] = []

        def worker() -> None:
            for _ in range(20):
                results.append(limiter.allow("same", now=1.0))

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sum(results), 25)

    def test_rejects_non_positive_settings(self) -> None:
        for kwargs in ({"limit": 0}, {"limit": 1, "window_seconds": 0}, {"limit": 1, "max_keys": 0}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    limiter_mod.SlidingWindowLimiter(**kwargs)


class _Echo(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        body = limits_mod.read_limited_body(self, 100)
        if body is None:
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        return


class _Stub:
    """Minimal handler stand-in for header values http.client cannot send."""

    def __init__(self, declared: list[str]) -> None:
        self.headers = self
        self._declared = declared
        self.errors: list[int] = []

    def get(self, name: str, default: object = None) -> object:
        return default

    def get_all(self, name: str) -> list[str]:
        return list(self._declared)

    def send_error(self, code: int, message: str = "") -> None:
        self.errors.append(code)


class ReadLimitedBodyTests(unittest.TestCase):
    def _request(self, headers: dict[str, str], body: bytes = b"") -> int:
        server = HTTPServer(("127.0.0.1", 0), _Echo)
        server.daemon_threads = True
        threading.Thread(target=server.serve_forever, daemon=True).start()
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        try:
            conn.putrequest("POST", "/", skip_accept_encoding=True)
            for key, value in headers.items():
                conn.putheader(key, value)
            conn.endheaders(body)
            return conn.getresponse().status
        finally:
            conn.close()
            server.shutdown()
            server.server_close()

    def test_body_within_the_limit_is_returned(self) -> None:
        self.assertEqual(self._request({"Content-Length": "5"}, b"hello"), 200)

    def test_declared_oversize_is_refused_before_reading(self) -> None:
        self.assertEqual(self._request({"Content-Length": "101"}), 413)

    def test_negative_and_non_plain_lengths_are_client_errors(self) -> None:
        for value in ("-1", "+5", "1_0", "5.0"):
            with self.subTest(value=value):
                self.assertEqual(self._request({"Content-Length": value}), 400)

    def test_non_numeric_length_is_a_client_error(self) -> None:
        self.assertEqual(self._request({"Content-Length": "abc"}), 400)

    def test_values_that_cannot_travel_over_http_client_are_refused_by_the_helper_itself(self) -> None:
        arabic_five = chr(0x0665)
        fullwidth_five = chr(0xFF15)
        for value in (" 5", "5 ", arabic_five, fullwidth_five, "", "9" * 21, "9" * 5000):
            with self.subTest(value=value[:12]):
                stub = _Stub([value])
                self.assertIsNone(limits_mod.read_limited_body(stub, 100))
                self.assertEqual(stub.errors, [400])

    def test_duplicate_content_length_headers_are_refused(self) -> None:
        stub = _Stub(["5", "5"])
        self.assertIsNone(limits_mod.read_limited_body(stub, 100))
        self.assertEqual(stub.errors, [400])

    def test_missing_length_is_refused(self) -> None:
        self.assertEqual(self._request({}), 411)

    def test_chunked_bodies_are_refused(self) -> None:
        self.assertEqual(self._request({"Transfer-Encoding": "chunked"}), 411)


class BindHostTests(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = os.environ.pop("TPL_HOST", None)

    def tearDown(self) -> None:
        os.environ.pop("TPL_HOST", None)
        if self._saved is not None:
            os.environ["TPL_HOST"] = self._saved

    def test_default_is_loopback_without_warning(self) -> None:
        self.assertEqual(bind_mod.resolve_host("TPL_HOST"), ("127.0.0.1", None))

    def test_blank_value_falls_back_to_the_default(self) -> None:
        os.environ["TPL_HOST"] = "   "
        self.assertEqual(bind_mod.resolve_host("TPL_HOST"), ("127.0.0.1", None))

    def test_opt_in_returns_the_host_and_a_warning(self) -> None:
        os.environ["TPL_HOST"] = "0.0.0.0"
        host, warning = bind_mod.resolve_host("TPL_HOST")
        self.assertEqual(host, "0.0.0.0")
        self.assertIn("0.0.0.0", warning)

    def test_explicit_loopback_names_do_not_warn(self) -> None:
        os.environ["TPL_HOST"] = "localhost"
        self.assertEqual(bind_mod.resolve_host("TPL_HOST"), ("localhost", None))


class TemplatesPassTheirOwnScannersTests(unittest.TestCase):
    def test_both_scanners_report_nothing_for_the_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("rate_limiter.py", "request_limits.py", "bind_host.py"):
                shutil.copy(TEMPLATES / name, Path(tmp) / name)
            self.assertEqual(check_exposure_hotspots.scan(Path(tmp)), [])
            self.assertEqual(check_security_hotspots.scan(Path(tmp)), [])


if __name__ == "__main__":
    unittest.main()
