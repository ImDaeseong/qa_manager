"""Create a starter checklist for a new project, with the exposure/availability check already registered.

Usage: python scripts/new_project.py <project-name> <repo-root-relative-to-Desktop>

A project that is never registered is never scanned, so registration is where
SECURITY_NETWORK_QA_STANDARD.md's network-exposure rules would otherwise get dropped. The starter
carries the one check that already exists and runs (scripts/check_exposure_hotspots.py); add the
project's own tests and guards afterwards -- do not invent checks that have no command behind them.

The script only writes projects/<name>/checklist.yaml. Public-HTML review (PUBLIC_PROJECTS in
scripts/_checklist_lib.py) and the project counts in README.md/ELI5.html stay manual steps.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

QA_ROOT = Path(__file__).resolve().parent.parent
DESKTOP = QA_ROOT.parent
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")

TEMPLATE = """project: {name}
repo_root: "{repo_root}"
updated: {today}
requirements:
  - id: R1
    quality_dimension: security
    description: "서버 코드가 모든 인터페이스(0.0.0.0) 바인딩, 크기 상한 없는 요청 바디 읽기, 속도 제한 없는 외부 노출을 미검토 상태로 남기면 안 된다"
    dev_items:
      - id: R1-D1
        description: "노출면·가용성 정적 패턴 스캐너(qa_manager/scripts/check_exposure_hotspots.py)"
        test_items:
          - id: exposure-hotspots-guard
            category: basic
            description: "CWE-1327/CWE-770/CWE-400 패턴이 qa:allow 사유 없이 남아있지 않은지 확인합니다. 정적 패턴만 보며 앞단 프록시/WAF 유무는 보지 못합니다."
            check: "python {up}qa_manager/scripts/check_exposure_hotspots.py ."
            status: pending
"""


def create(name: str, repo_root: str, qa_root: Path = QA_ROOT, desktop: Path = DESKTOP) -> Path:
    """Write the starter checklist and return its path; refuse unsafe names, unknown repos, and overwrites."""
    if not NAME.fullmatch(name):
        raise ValueError(f"invalid project name: {name!r}")
    repo = (desktop / repo_root).resolve()
    if desktop.resolve() not in repo.parents or not repo.is_dir():
        raise ValueError(f"repo_root must be an existing folder below the Desktop root: {repo_root!r}")
    target = qa_root / "projects" / name / "checklist.yaml"
    if target.exists():
        raise FileExistsError(f"{target} already exists; edit it instead of regenerating")
    relative = repo.relative_to(desktop.resolve())
    up = "../" * len(relative.parts)  # checks run with the repo as cwd; qa_manager sits beside the Desktop-level folders
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        TEMPLATE.format(name=name, repo_root=relative.as_posix(), up=up, today=date.today().isoformat()),
        encoding="utf-8",
    )
    return target


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    try:
        target = create(argv[0], argv[1])
    except (ValueError, FileExistsError) as error:
        print(f"FAIL: {error}")
        return 1
    print(f"CREATED {target}")
    print("Next (manual): add the project's real tests/guards as test_items, review public-HTML exposure and add the")
    print("name to PUBLIC_PROJECTS in scripts/_checklist_lib.py, update the project counts in README.md/ELI5.html,")
    print("then run python scripts/generate_system_index.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
