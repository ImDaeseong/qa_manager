"""Regression tests for templates/errors/boundary_errors.py (the boundary-aware error record)."""

from __future__ import annotations

import importlib.util
import json
import logging
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "errors" / "boundary_errors.py"
sys.path.insert(0, str(ROOT / "scripts"))

import check_error_handling_hotspots
import check_exposure_hotspots
import check_security_hotspots

spec = importlib.util.spec_from_file_location("tpl_boundary_errors", TEMPLATE)
be = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = be
spec.loader.exec_module(be)


class _Http(Exception):
    def __init__(self, status: int) -> None:
        super().__init__(f"http {status}")
        self.status_code = status


class _Records(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _logger() -> tuple[logging.Logger, _Records]:
    logger = logging.getLogger(f"tpl-{id(object())}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    records = _Records()
    logger.addHandler(records)
    return logger, records


class ClassifyTests(unittest.TestCase):
    def test_kinds_by_type_and_status(self) -> None:
        cases = [
            (TimeoutError("t"), "timeout"),
            (subprocess.TimeoutExpired("cmd", 1), "timeout"),
            (PermissionError("p"), "auth"),
            (_Http(401), "auth"),
            (_Http(403), "auth"),
            (_Http(429), "rate_limit"),
            (_Http(503), "provider"),
            (json.JSONDecodeError("m", "d", 0), "parse"),
            (UnicodeDecodeError("utf-8", b"x", 0, 1, "r"), "parse"),
            (FileNotFoundError("f"), "io"),
            (KeyError("k"), "unknown"),
        ]
        for exc, kind in cases:
            with self.subTest(exc=type(exc).__name__, kind=kind):
                self.assertEqual(be.classify(exc), kind)

    def test_every_returned_kind_is_declared(self) -> None:
        self.assertTrue({be.classify(e) for e in (TimeoutError(), _Http(429), KeyError())} <= set(be.KINDS))


class CallBoundaryTests(unittest.TestCase):
    def test_success_returns_the_value(self) -> None:
        self.assertEqual(be.call_boundary("m.f", "disk", lambda a, b=0: a + b, 1, b=2), 3)

    def test_failure_becomes_a_boundary_error_with_the_original_as_cause(self) -> None:
        def fail() -> None:
            raise FileNotFoundError("missing.json")

        with self.assertRaises(be.BoundaryError) as ctx:
            be.call_boundary("config.load", "disk", fail)
        error = ctx.exception
        self.assertEqual((error.unit, error.boundary, error.kind), ("config.load", "disk", "io"))
        self.assertIsInstance(error.__cause__, FileNotFoundError)
        self.assertIn("missing.json", str(error))

    def test_failure_is_logged_exactly_once_even_through_nested_boundaries(self) -> None:
        logger, records = _logger()

        def inner() -> None:
            raise _Http(503)

        def outer() -> None:
            be.call_boundary("a.inner", "network", inner, logger=logger)

        with self.assertRaises(be.BoundaryError) as ctx:
            be.call_boundary("b.outer", "service", outer, logger=logger)
        self.assertEqual(len(records.records), 1)
        self.assertEqual(ctx.exception.unit, "a.inner")  # the inner identification is kept, not overwritten
        self.assertEqual(ctx.exception.kind, "provider")
        self.assertTrue(ctx.exception.logged)

    def test_without_a_logger_nothing_is_logged_and_the_error_still_carries_context(self) -> None:
        with self.assertRaises(be.BoundaryError) as ctx:
            be.call_boundary("u", "b", lambda: 1 / 0)
        self.assertFalse(ctx.exception.logged)
        self.assertEqual(ctx.exception.kind, "unknown")

    def test_custom_classifier_is_used(self) -> None:
        with self.assertRaises(be.BoundaryError) as ctx:
            be.call_boundary("u", "b", lambda: 1 / 0, classifier=lambda exc: "contract")
        self.assertEqual(ctx.exception.kind, "contract")

    def test_unknown_kind_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            be.BoundaryError("u", "b", "weird")

    def test_keyboard_interrupt_is_not_swallowed_or_wrapped(self) -> None:
        def interrupted() -> None:
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            be.call_boundary("u", "b", interrupted)


class AsyncAndClassifierTests(unittest.TestCase):
    def test_async_call_is_wrapped_and_awaited(self) -> None:
        import asyncio

        async def ok() -> int:
            return 7

        async def fail() -> None:
            raise TimeoutError("slow")

        self.assertEqual(asyncio.run(be.call_boundary_async("u", "net", ok)), 7)
        with self.assertRaises(be.BoundaryError) as ctx:
            asyncio.run(be.call_boundary_async("u", "net", fail))
        self.assertEqual(ctx.exception.kind, "timeout")
        self.assertIsInstance(ctx.exception.__cause__, TimeoutError)

    def test_a_classifier_returning_an_unknown_kind_does_not_hide_the_failure(self) -> None:
        with self.assertRaises(be.BoundaryError) as ctx:
            be.call_boundary("u", "b", lambda: 1 / 0, classifier=lambda exc: "bogus")
        self.assertEqual(ctx.exception.kind, "unknown")
        self.assertIsInstance(ctx.exception.__cause__, ZeroDivisionError)


class ErrorChainTests(unittest.TestCase):
    def test_chain_lists_outer_error_first_and_root_cause_last(self) -> None:
        try:
            be.call_boundary("a.load", "disk", lambda: json.loads("{"))
        except be.BoundaryError as error:
            lines = be.error_chain(error)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("a.load -> disk [parse]"))
        self.assertTrue(lines[1].startswith("JSONDecodeError"))

    def test_chain_honors_raise_from_none(self) -> None:
        try:
            try:
                raise KeyError("inner")
            except KeyError:
                raise ValueError("suppressed") from None
        except ValueError as error:
            lines = be.error_chain(error)
        self.assertEqual(len(lines), 1)

    def test_chain_handles_a_cycle_without_looping(self) -> None:
        first, second = RuntimeError("one"), RuntimeError("two")
        first.__cause__ = second
        second.__cause__ = first
        self.assertEqual(len(be.error_chain(first)), 2)


class ExpectShapeTests(unittest.TestCase):
    SHAPE = {"id": int, "name": str, "tags": [str], "meta": {"score": (int, float)}}

    def test_valid_data_passes(self) -> None:
        be.expect_shape({"id": 1, "name": "x", "tags": ["a"], "meta": {"score": 0.5}, "extra": True}, self.SHAPE, "api.parse")

    def test_each_violation_is_reported_as_a_contract_error_naming_the_path(self) -> None:
        cases = [
            ({"name": "x", "tags": [], "meta": {"score": 1}}, "id: missing"),
            ({"id": "1", "name": "x", "tags": [], "meta": {"score": 1}}, "id: expected int, got str"),
            ({"id": 1, "name": None, "tags": [], "meta": {"score": 1}}, "name: expected str, got None"),
            ({"id": 1, "name": "x", "tags": ["a", 2], "meta": {"score": 1}}, "tags[1]: expected str, got int"),
            ({"id": 1, "name": "x", "tags": [], "meta": {}}, "meta.score: missing"),
            ({"id": 1, "name": "x", "tags": [], "meta": []}, "meta: expected an object, got list"),
            ([], "<root>: expected an object, got list"),
        ]
        for data, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(be.BoundaryError) as ctx:
                    be.expect_shape(data, self.SHAPE, "api.parse")
                self.assertEqual(ctx.exception.kind, "contract")
                self.assertIn(expected, ctx.exception.detail)


class ExpectShapeEdgeCaseTests(unittest.TestCase):
    def test_empty_list_shape_accepts_any_list(self) -> None:
        be.expect_shape({"a": [1, "x"]}, {"a": []}, "u")
        with self.assertRaises(be.BoundaryError):
            be.expect_shape({"a": "x"}, {"a": []}, "u")

    def test_bool_is_not_accepted_for_int_unless_allowed(self) -> None:
        with self.assertRaises(be.BoundaryError):
            be.expect_shape({"a": True}, {"a": int}, "u")
        be.expect_shape({"a": True}, {"a": (int, bool)}, "u")

    def test_optional_fields_are_expressed_with_none_type(self) -> None:
        be.expect_shape({"a": None}, {"a": (str, type(None))}, "u")
        be.expect_shape({"a": "x"}, {"a": (str, type(None))}, "u")
        with self.assertRaises(be.BoundaryError):
            be.expect_shape({"a": 3}, {"a": (str, type(None))}, "u")

    def test_an_invalid_shape_is_a_programming_error_not_a_contract_error(self) -> None:
        with self.assertRaises(TypeError):
            be.expect_shape({"a": 1}, {"a": "int"}, "u")


class TemplatePassesItsOwnScannersTests(unittest.TestCase):
    def test_all_three_scanners_report_nothing_for_the_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(TEMPLATE, Path(tmp) / "boundary_errors.py")
            self.assertEqual(check_security_hotspots.scan(Path(tmp)), [])
            self.assertEqual(check_exposure_hotspots.scan(Path(tmp)), [])
            findings, _ = check_error_handling_hotspots.scan(Path(tmp))
            self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
