"""Shared helpers for reading and running a project's projects/<name>/checklist.yaml.

Used by run_checklist.py (terminal report) and generate_checklist_dashboard.py
(static HTML report), both in this same qa_manager/scripts/ folder. Both need
the same "load the hierarchy, run each leaf test_item's `check` command live,
in that project's own repo" logic, so it lives here once instead of twice.

qa_manager is a standalone system that inspects several independent sibling
repos (hermes-agents, ai_prompt, ai-workspace, ai_test1, skills, ...), so
there is no single project root to default `check` commands into. Each
project's checklist.yaml must declare `repo_root`: the path to that project's
own repo, relative to DESKTOP_ROOT (qa_manager's parent folder — the common
ancestor all these sibling repos share on this machine).
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import yaml

QA_ROOT = Path(__file__).resolve().parent.parent
DESKTOP_ROOT = QA_ROOT.parent
DEFAULT_CHECKLIST = QA_ROOT / "projects" / "hermes-agents" / "checklist.yaml"

# No `check` command observed across any registered project takes more than a
# couple of minutes (the slowest today is CareerDiff's `npm run build`). This
# is a safety net against a hung command (waiting on stdin, a server that
# never exits, a bug in the target project itself) blocking the whole run
# forever with no way out short of killing the process by hand.
CHECK_TIMEOUT_SECONDS = 300
MAX_OUTPUT_CHARS = 20_000

_SECRET_ENV_MARKERS = (
    "API_KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "PRIVATE_KEY",
)
_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(
        r"(?i)\b([A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)[A-Z0-9_]*)"
        r"\s*[:=]\s*([^\s,;]+)"
    ),
)


def load(path: Path = DEFAULT_CHECKLIST) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def project_root(data: dict) -> Path:
    """Resolve a checklist's `repo_root` (relative to DESKTOP_ROOT) to an absolute path."""
    repo_root = data.get("repo_root")
    if not repo_root:
        raise ValueError(
            f"checklist for project {data.get('project')!r} is missing required `repo_root`"
        )
    resolved = (DESKTOP_ROOT / repo_root).resolve()
    if resolved == DESKTOP_ROOT or DESKTOP_ROOT not in resolved.parents:
        raise ValueError("repo_root must resolve to a project below DESKTOP_ROOT")
    if not resolved.is_dir():
        raise ValueError(f"repo_root does not exist or is not a directory: {repo_root}")
    return resolved


def sanitized_environment(source: dict[str, str] | None = None) -> dict[str, str]:
    """Return a child-process environment with credential-like variables removed."""
    source = os.environ if source is None else source
    return {
        key: value
        for key, value in source.items()
        if not any(marker in key.upper() for marker in _SECRET_ENV_MARKERS)
    }


def sanitize_output(output: str) -> str:
    """Redact credential-shaped text and cap output before it reaches reports."""
    redacted = output
    redacted = _SECRET_PATTERNS[0].sub("[REDACTED_API_KEY]", redacted)
    redacted = _SECRET_PATTERNS[1].sub(r"\1 [REDACTED]", redacted)
    redacted = _SECRET_PATTERNS[2].sub(r"\1=[REDACTED]", redacted)
    if len(redacted) > MAX_OUTPUT_CHARS:
        return redacted[:MAX_OUTPUT_CHARS] + "\n[OUTPUT_TRUNCATED]"
    return redacted


def validate_check_command(check_cmd: object) -> str:
    """Accept one trusted local checklist command without hidden extra lines."""
    if not isinstance(check_cmd, str) or not check_cmd.strip():
        raise ValueError("test_item check must be a non-empty string")
    if "\x00" in check_cmd or "\r" in check_cmd or "\n" in check_cmd:
        raise ValueError("test_item check must be a single line without NUL bytes")
    return check_cmd


def run_test_item(item: dict, cwd: Path) -> tuple[str, str]:
    """Run one test_item's `check` command now, inside `cwd`. Returns (live_status, output).

    Uses Popen (not subprocess.run) because on Windows, `shell=True` runs the
    command through a cmd.exe wrapper: subprocess.run's own timeout only
    kills that wrapper, not the real child process it launched (e.g. a
    long-running python/node process) — the child keeps running and holding
    the stdout/stderr pipes open, so `communicate()` still blocks until the
    child finishes on its own. Reproduced directly: a 10s sleep with a 2s
    timeout still took the full 10s. `taskkill /T` below kills the whole
    process tree (wrapper + child), which actually unblocks the pipes.
    """
    check_cmd = item.get("check")
    if not check_cmd:
        return "pending", ""
    try:
        check_cmd = validate_check_command(check_cmd)
    except ValueError as exc:
        return "fail", f"INVALID CHECK: {exc}"
    proc = subprocess.Popen(
        check_cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,  # qa:allow CWE-78 - check_cmd is operator-authored checklist.yaml, not external input
        text=True, encoding="utf-8", errors="replace",
        env=sanitized_environment(),
    )
    try:
        output, _ = proc.communicate(timeout=CHECK_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True, timeout=15,
        )
        partial, _ = proc.communicate()
        return "fail", sanitize_output(
            f"TIMEOUT: check did not finish within {CHECK_TIMEOUT_SECONDS}s, "
            f"process tree killed.\n{partial}"
        )
    live_status = "pass" if proc.returncode == 0 else "fail"
    return live_status, sanitize_output(output)


def iter_test_items(data: dict):
    """Yield (requirement, dev_item, test_item) for every leaf in the hierarchy."""
    for req in data.get("requirements", []):
        for dev_item in req.get("dev_items", []):
            for test_item in dev_item.get("test_items", []):
                yield req, dev_item, test_item
