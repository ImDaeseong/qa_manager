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

import subprocess
from pathlib import Path

import yaml

QA_ROOT = Path(__file__).resolve().parent.parent
DESKTOP_ROOT = QA_ROOT.parent
DEFAULT_CHECKLIST = QA_ROOT / "projects" / "hermes-agents" / "checklist.yaml"


def load(path: Path = DEFAULT_CHECKLIST) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def project_root(data: dict) -> Path:
    """Resolve a checklist's `repo_root` (relative to DESKTOP_ROOT) to an absolute path."""
    repo_root = data.get("repo_root")
    if not repo_root:
        raise ValueError(
            f"checklist for project {data.get('project')!r} is missing required `repo_root`"
        )
    return (DESKTOP_ROOT / repo_root).resolve()


def run_test_item(item: dict, cwd: Path) -> tuple[str, str]:
    """Run one test_item's `check` command now, inside `cwd`. Returns (live_status, output)."""
    check_cmd = item.get("check")
    if not check_cmd:
        return "pending", ""
    result = subprocess.run(
        check_cmd, shell=True, cwd=cwd, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    live_status = "pass" if result.returncode == 0 else "fail"
    return live_status, result.stdout + result.stderr


def iter_test_items(data: dict):
    """Yield (requirement, dev_item, test_item) for every leaf in the hierarchy."""
    for req in data.get("requirements", []):
        for dev_item in req.get("dev_items", []):
            for test_item in dev_item.get("test_items", []):
                yield req, dev_item, test_item
