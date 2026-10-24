"""Static scan for error handlers that detect an error and then do nothing about it (see ERROR_BOUNDARY_QA_STANDARD.md).

Usage: python scripts/check_error_handling_hotspots.py [path]   (default: current directory)

Yuan et al. (OSDI 2014) traced 92% of the catastrophic failures they studied to incorrect handling of
non-fatal errors that the software had explicitly signalled, and named three trivially detectable patterns:
a handler that is empty or only logs, a handler that aborts on an overly general exception, and a handler
that carries a TODO/FIXME. This scanner checks the two of those that a static pattern can see:

  CWE-390  a broad handler (bare `except`, `Exception`, `BaseException`, JS `catch`) whose body does nothing:
           empty, only logs, or only continues/returns a constant
  CWE-755  a TODO/FIXME comment inside a handler

A narrow handler that swallows a specific exception (e.g. `except FileNotFoundError: pass`) is counted and
reported as information but does not fail the check: it is often a deliberate best-effort step, and the
failure condition is named. Acknowledge an accepted broad handler with a same-line `qa:allow CWE-390 - <reason>`
comment on the `except`/`catch` line.

Pattern matching only: it cannot tell whether doing nothing is correct, only that nobody wrote down why.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_exposure_hotspots import TEST_PATH, candidate_files  # noqa: E402
from check_security_hotspots import ALLOW_MARKER  # noqa: E402

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SELF_EXCLUDE = {"check_error_handling_hotspots.py", "test_error_handling_hotspots.py"}
LOG_NAMES = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}  # print is the user-facing channel of a CLI script, not a log
BROAD = {"Exception", "BaseException"}
USER_FACING = {"st", "streamlit", "messagebox", "flash"}
TODO = re.compile(r"(?i)\b(?:todo|fixme)\b")
JS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
# Minified or third-party bundles are not code this project maintains.
VENDORED = re.compile(r"(?i)(?:\.min\.|\.bundle\.|(?:^|[\\/])(?:vendor|third_party|node_modules|dist|build|\.next|report-html-files)[\\/])")
JS_EMPTY_CATCH = re.compile(r"catch\s*(?:\([^)]*\))?\s*\{(?:\s|//[^\n]*|/\*.*?\*/)*\}", re.S)
JS_EMPTY_PROMISE_CATCH = re.compile(r"\.catch\(\s*(?:\([^)]*\)|\w+)?\s*=>\s*\{\s*\}\s*\)")

HINT_BROAD = "예외를 구체적으로 좁히거나, 실패를 호출자에게 알리거나(다시 raise·결과로 반환), 의도라면 같은 줄에 `qa:allow CWE-390 - <사유>`를 남기세요."
HINT_TODO = "핸들러의 TODO/FIXME를 처리하거나 이슈로 옮기고, 처리 전에는 오류를 삼키지 않도록 하세요."


def _is_log_call(stmt: ast.stmt) -> bool:
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        func = stmt.value.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in USER_FACING:
            return False  # shown to the user (e.g. st.error): the failure is reported, not swallowed
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        return name in LOG_NAMES
    return False


def _signals_failure(stmt: ast.stmt) -> bool:
    """A constant return that tells the caller it failed: a non-zero exit code or True-valued marker."""
    return (
        isinstance(stmt, ast.Return)
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, int)
        and not isinstance(stmt.value.value, bool)
        and stmt.value.value != 0
    )


def _does_nothing(body: list[ast.stmt]) -> bool:
    """True when every statement is pass/docstring, a log call, continue, or a bare/constant return."""
    for stmt in body:
        if isinstance(stmt, (ast.Pass, ast.Continue, ast.Break)) or _is_log_call(stmt):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            continue
        if _signals_failure(stmt):
            return False
        if isinstance(stmt, ast.Return) and (stmt.value is None or isinstance(stmt.value, ast.Constant)):
            continue
        return False
    return True


def _is_broad(handler: ast.ExceptHandler) -> bool:
    caught = handler.type
    if caught is None:
        return True
    names = []
    for node in caught.elts if isinstance(caught, ast.Tuple) else [caught]:
        names.append(node.id if isinstance(node, ast.Name) else getattr(node, "attr", ""))
    return any(name in BROAD for name in names)


def scan_python(rel: str, text: str) -> tuple[list[str], int]:
    """Return (findings, count of acknowledged-narrow swallows); a file that does not parse is skipped (see scan)."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [], -1
    lines = text.splitlines()
    findings: list[str] = []
    narrow = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        head_end = node.body[0].lineno if node.body else node.lineno  # the except clause plus its first statement
        head = "\n".join(lines[node.lineno - 1:head_end])
        segment = "\n".join(lines[node.lineno - 1:(node.end_lineno or node.lineno)])
        acknowledged = ALLOW_MARKER in head
        if _does_nothing(node.body):
            if _is_broad(node):
                if not acknowledged:
                    findings.append(f"{rel}:{node.lineno}: [CWE-390] 넓은 예외를 잡고도 아무 조치를 하지 않음 - {HINT_BROAD}")
            else:
                narrow += 1
        if TODO.search(segment) and not acknowledged:
            findings.append(f"{rel}:{node.lineno}: [CWE-755] 오류 핸들러 안에 TODO/FIXME가 있음 - {HINT_TODO}")
    return findings, narrow


def scan_js(rel: str, text: str) -> list[str]:
    findings: list[str] = []
    for pattern in (JS_EMPTY_CATCH, JS_EMPTY_PROMISE_CATCH):
        for match in pattern.finditer(text):
            lineno = text.count("\n", 0, match.start()) + 1
            line = text.splitlines()[lineno - 1] if lineno <= len(text.splitlines()) else ""
            if ALLOW_MARKER not in line:
                findings.append(f"{rel}:{lineno}: [CWE-390] 비어 있는 catch로 오류를 삼킴 - {HINT_BROAD}")
    return findings


def scannable_files(root: Path) -> list[Path]:
    """Python and JS/TS source this project maintains: not tests, vendored bundles, or this scanner itself."""
    found = []
    for path in candidate_files(root):
        if path.name in SELF_EXCLUDE or path.name == "conftest.py" or not path.is_file():
            continue
        if path.suffix.lower() != ".py" and path.suffix.lower() not in JS_EXTENSIONS:
            continue
        rel = str(path.relative_to(root))
        if TEST_PATH.search(rel) or VENDORED.search(rel):
            continue
        found.append(path)
    return found


def scan(root: Path) -> tuple[list[str], int]:
    findings: list[str] = []
    narrow_total = 0
    unparsable = 0
    for path in scannable_files(root):
        suffix = path.suffix.lower()
        rel = str(path.relative_to(root))
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")  # a BOM would make ast.parse reject the file
        except OSError:
            continue
        if suffix == ".py":
            found, narrow = scan_python(rel, text)
            findings.extend(found)
            if narrow < 0:
                unparsable += 1
            else:
                narrow_total += narrow
        else:
            findings.extend(scan_js(rel, text))
    scan.unparsable = unparsable  # exposed for main(): files skipped because they do not parse
    return findings, narrow_total


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    findings, narrow = scan(root)
    if findings:
        print(f"FAIL: {len(findings)} unacknowledged error-handling hotspot(s) found:")
        for line in findings:
            print(f"  {line}")
        print("Acknowledge an accepted risk with a same-line `qa:allow CWE-390 - <reason>` comment on the except/catch line, or fix it.")
    else:
        print("PASS: no unacknowledged error-handling hotspots found (static pattern scan only)")
    print(f"INFO: {narrow} narrow handler(s) swallow a named exception without action (review, not a failure)")
    if getattr(scan, "unparsable", 0):
        print(f"INFO: {scan.unparsable} Python file(s) did not parse and were not checked")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
