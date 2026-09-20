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
import platform
import re
import subprocess
import tempfile
from pathlib import Path

import yaml

QA_ROOT = Path(__file__).resolve().parent.parent
DESKTOP_ROOT = QA_ROOT.parent
DEFAULT_CHECKLIST = QA_ROOT / "projects" / "hermes-agents" / "checklist.yaml"
PUBLIC_PROJECTS = frozenset({
    "ai-workspace", "ai_agent", "ai_prompt", "ai_test", "ai_test1", "ai_test2",
    "hermes-agents", "qa_manager", "skills",
})

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
_PRIVATE_REPORT_PATTERNS = (
    re.compile(r"(?i)\b[A-Z]:[\\/]Users[\\/][^\\/\s<]+"),
    re.compile(r"/(?:Users|home)/[^/\s<]+"),
)


def load(path: Path = DEFAULT_CHECKLIST) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_public_project(path: Path) -> None:
    """Require an explicit public-project review before generating publishable HTML."""
    resolved = path.resolve()
    if resolved.parent.parent != (QA_ROOT / "projects").resolve() or resolved.parent.name not in PUBLIC_PROJECTS:
        raise ValueError(f"PUBLIC_PROJECT_UNREVIEWED: {resolved.parent.name}")


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


def write_public_report(path: Path, content: str) -> None:
    """Reject obvious private data and replace a complete public report atomically."""
    if any(pattern.search(content) for pattern in (*_PRIVATE_REPORT_PATTERNS, *_SECRET_PATTERNS)):
        raise ValueError("PUBLIC_REPORT: private path or credential-shaped text detected")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


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
    timeout still took the full 10s. `taskkill /T` on timeout kills the whole
    process tree (wrapper + child), which actually unblocks the pipes. This
    tool otherwise only runs for real on Windows (see open_qa_system.bat), but
    this repo's own test suite runs in CI on Linux too (.github/workflows/
    validate.yml) — a `proc.kill()` fallback there keeps a hung-command test
    from crashing on a missing `taskkill` binary instead of degrading to an
    ordinary timeout failure.
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
        if platform.system() == "Windows":
            # taskkill /T kills the whole process tree; see the docstring above for
            # why the wrapper-only kill that proc.kill() would do isn't enough here.
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True, timeout=15,
            )
        else:
            # No `shell=True` wrapper-vs-child split on POSIX the way there is on
            # Windows, so killing the direct child is enough (this tool otherwise
            # only ever runs for real on Windows -- see open_qa_system.bat -- this
            # branch exists so a hang on another OS, e.g. this repo's Linux CI,
            # degrades to a normal timeout failure instead of an unhandled
            # FileNotFoundError from invoking the Windows-only `taskkill`).
            proc.kill()
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


# Release-review areas from RELEASE_READINESS_STANDARD.md. A requirement may link a live
# check to one area via `quality_dimension`; a check passing is only partial evidence.
COMMERCIAL_DIMENSIONS: dict[str, str] = {
    "functional_suitability": "기능 적합성 — 주요 사용자 작업과 정확성",
    "performance_efficiency": "성능 효율성 — 응답 시간·자원·용량",
    "compatibility": "호환성 — 지원 환경과 연동",
    "interaction_capability": "상호작용 능력 — 사용성·포용성·접근성",
    "reliability": "신뢰성 — 장애 처리·복구·가용성",
    "security": "보안 — 위협·권한·입력·비밀정보 검증",
    "maintainability": "유지보수성 — 변경·진단·검증 가능성",
    "portability": "유연성·이식성 — 설치·환경 적응·확장",
    "safety": "안전성 — 위해·오용 위험과 실패 시 안전",
    "quality_in_use": "실사용 품질 — 실제 사용자·맥락에서의 결과",
    "privacy": "개인정보·데이터 거버넌스 — 수집·보관·삭제·권리",
    "supply_chain": "공급망·라이선스 — 구성요소·취약점·배포 권리",
    "operations": "배포·운영 — 재현 빌드·관측·백업·롤백·지원",
    "legal": "법률·규제 — 판매 지역·산업별 의무와 계약",
    "commercial": "사업 운영 — 가격·결제·환불·고객 지원",
}
NOT_APPLICABLE_AREAS = {"privacy"}  # No personal-data processing may be evidenced.


def commercial_readiness(data: dict, req_statuses: dict[str, str]) -> dict:
    """Combine live checks and human evidence into a release-review status.

    Live checks are useful evidence, but their tags alone cannot certify a whole quality area.
    A release review must name the release scope, provide evidence for every area, and record a
    human approval. Missing review evidence keeps the release decision on hold.
    """
    dimensions: dict[str, dict] = {
        key: {"label": label, "requirement_ids": [], "status": "missing"}
        for key, label in COMMERCIAL_DIMENSIONS.items()
    }
    for req in data.get("requirements", []):
        dim = req.get("quality_dimension")
        if dim in dimensions:
            dimensions[dim]["requirement_ids"].append(req.get("id", ""))

    review = data.get("release_review") or {}
    areas = review.get("areas") or {}
    for key, info in dimensions.items():
        checks = [req_statuses.get(rid) for rid in info["requirement_ids"]]
        decision = areas.get(key) or {}
        info["evidence"] = decision.get("evidence", "")
        if any(status == "fail" for status in checks):
            info["status"] = "failing"
        elif not decision.get("evidence"):
            info["status"] = "pending_review" if checks else "missing"
        elif decision.get("decision") == "pass" and all(status == "pass" for status in checks):
            info["status"] = "covered"
        elif (key in NOT_APPLICABLE_AREAS and decision.get("decision") == "not_applicable"
              and decision.get("reason") and not checks):
            info["status"] = "not_applicable"
        else:
            info["status"] = "pending_review"

    gaps = [key for key, info in dimensions.items()
            if info["status"] not in {"covered", "not_applicable"}]
    approval = review.get("approval") or {}
    approved = all(review.get(field) for field in ("release", "audience", "distribution", "jurisdictions")) and all(
        approval.get(field) for field in ("reviewer", "date", "evidence")
    )
    return {"dimensions": dimensions, "ready": not gaps and approved,
            "gaps": gaps, "approval_missing": not approved}
