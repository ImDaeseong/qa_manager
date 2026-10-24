"""Boundary-aware errors: say which unit failed at which boundary, why, and what caused it (stdlib only, copy into your project).

A large share of faults in the interface-fault studies this repository cites (39% to 49%) sit where one unit calls
another or crosses into I/O, a process, the network or a parser (see ERROR_BOUNDARY_QA_STANDARD.md). `call_boundary` wraps such a call so a failure
carries a unit identifier, the boundary it crossed, a low-cardinality failure kind and the original exception as its
cause, and is logged exactly once where it crosses. `expect_shape` checks the data that crosses a boundary.

The kinds follow the failure tags AGENTS.md already asks for (timeout, rate limit, auth, provider) plus parse, io and
contract. They are deliberately few so they can be counted and alerted on, like OpenTelemetry's `error.type`.

`call_boundary` wraps a synchronous call; use `call_boundary_async` for a coroutine function, otherwise the failure
surfaces later, unwrapped, when the coroutine is awaited.
"""

from __future__ import annotations

import json
import logging
import subprocess
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

KINDS = ("timeout", "rate_limit", "auth", "provider", "parse", "io", "contract", "unknown")


class BoundaryError(Exception):
    """A failure at a call boundary: `unit` called across `boundary` and it failed with `kind`."""

    def __init__(self, unit: str, boundary: str, kind: str, detail: str = "") -> None:
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}, got {kind!r}")
        self.unit = unit
        self.boundary = boundary
        self.kind = kind
        self.detail = detail
        self.logged = False
        super().__init__(f"[{kind}] {unit} -> {boundary}: {detail}")


def classify(exc: BaseException) -> str:
    """Map an exception to one of KINDS using its type and any HTTP-like status code it carries."""
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None) or getattr(getattr(exc, "response", None), "status_code", None)
    if isinstance(status, int):
        if status == 429:
            return "rate_limit"
        if status in (401, 403):
            return "auth"
        if status >= 500:
            return "provider"
    if isinstance(exc, (TimeoutError, subprocess.TimeoutExpired)):
        return "timeout"
    if isinstance(exc, PermissionError):
        return "auth"
    if isinstance(exc, (json.JSONDecodeError, UnicodeDecodeError)):
        return "parse"
    if isinstance(exc, OSError):
        return "io"
    return "unknown"


def call_boundary(
    unit: str,
    boundary: str,
    func: Callable[..., Any],
    *args: Any,
    logger: logging.Logger | None = None,
    classifier: Callable[[BaseException], str] = classify,
    **kwargs: Any,
) -> Any:
    """Call `func`; on failure raise a BoundaryError from the original exception and log it once."""
    try:
        return func(*args, **kwargs)
    except BoundaryError:
        raise  # already identified and logged where it first crossed a boundary
    except Exception as exc:
        raise _wrap(unit, boundary, exc, logger, classifier) from exc


async def call_boundary_async(
    unit: str,
    boundary: str,
    func: Callable[..., Awaitable[Any]],
    *args: Any,
    logger: logging.Logger | None = None,
    classifier: Callable[[BaseException], str] = classify,
    **kwargs: Any,
) -> Any:
    """Await `func(...)`; on failure raise a BoundaryError from the original exception and log it once."""
    try:
        return await func(*args, **kwargs)
    except BoundaryError:
        raise
    except Exception as exc:
        raise _wrap(unit, boundary, exc, logger, classifier) from exc


def _wrap(unit: str, boundary: str, exc: Exception, logger: logging.Logger | None, classifier: Callable[[BaseException], str]) -> BoundaryError:
    kind = classifier(exc)
    if kind not in KINDS:  # a buggy classifier must not hide the real failure
        kind = "unknown"
    error = BoundaryError(unit, boundary, kind, f"{type(exc).__name__}: {exc}")
    if logger is not None:
        logger.error("boundary failure", exc_info=exc, extra={"unit": unit, "boundary": boundary, "kind": error.kind})
        error.logged = True
    return error


def error_chain(exc: BaseException) -> list[str]:
    """Render the cause chain from the outermost error to the root cause, one line per link."""
    lines: list[str] = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, BoundaryError):
            lines.append(f"{current.unit} -> {current.boundary} [{current.kind}] {current.detail}")
        else:
            lines.append(f"{type(current).__name__}: {current}")
        current = current.__cause__ or (None if current.__suppress_context__ else current.__context__)
    return lines


def expect_shape(data: Any, shape: Mapping[str, Any], unit: str, boundary: str = "contract") -> None:
    """Check that `data` has the keys in `shape` with the given types; nested dicts and [type] lists are supported."""
    problem = _shape_problem(data, shape, "")
    if problem:
        raise BoundaryError(unit, boundary, "contract", problem)


def _shape_problem(value: Any, expected: Any, path: str) -> str | None:
    where = path or "<root>"
    if isinstance(expected, Mapping):
        if not isinstance(value, Mapping):
            return f"{where}: expected an object, got {type(value).__name__}"
        for key, sub in expected.items():
            if key not in value:
                return f"{path + '.' if path else ''}{key}: missing"
            problem = _shape_problem(value[key], sub, f"{path + '.' if path else ''}{key}")
            if problem:
                return problem
        return None
    if isinstance(expected, list):
        if not isinstance(value, list):
            return f"{where}: expected a list, got {type(value).__name__}"
        for index, item in enumerate(value):
            if expected:  # [] means any list; [type] checks every item
                problem = _shape_problem(item, expected[0], f"{where}[{index}]")
                if problem:
                    return problem
        return None
    types = expected if isinstance(expected, tuple) else (expected,)
    if not all(isinstance(candidate, type) for candidate in types):
        raise TypeError(f"{where}: shape entries must be types, dicts or lists, got {expected!r}")
    if value is None:
        return None if type(None) in types else f"{where}: expected {_names(types)}, got None"
    if isinstance(value, bool) and bool not in types and int in types:
        return f"{where}: expected {_names(types)}, got bool"
    if not isinstance(value, types):
        return f"{where}: expected {_names(types)}, got {type(value).__name__}"
    return None


def _names(types: tuple[type, ...]) -> str:
    return " or ".join(candidate.__name__ for candidate in types)
