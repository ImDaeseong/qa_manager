"""Create a starter checklist for a new project, with the security scanners and its exposure tier already declared.

Usage: python scripts/new_project.py <project-name> <repo-root-relative-to-Desktop> [--exposure T0|T1|T2]

A project that is never registered is never scanned, so registration is where
SECURITY_NETWORK_QA_STANDARD.md's controls would otherwise get dropped. The starter carries the checks that
already exist and run (scripts/check_security_hotspots.py, check_exposure_hotspots.py, check_error_handling_hotspots.py and check_operational_readiness.py, all usable
on any repo) and records the project's exposure tier, which selects the controls the standard's matrix requires:

  T0  local only (127.0.0.1, one user)      T1  reachable from the same network (LAN/phone)
  T2  reachable from the public internet

Add the project's own tests and guards afterwards -- do not invent checks that have no command behind them.
Controls the scanners cannot see (authentication, authorization, uploads, SSRF, LLM/agent boundaries, an
upstream DDoS defense) stay human-review items in the standard; the tier tells the reviewer which ones apply.

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
TIERS = ("T0", "T1", "T2")

TEMPLATE = """project: {name}
repo_root: "{repo_root}"
exposure_tier: {tier}
updated: {today}
requirements:
  - id: R1
    quality_dimension: security
    description: "커밋되는 소스에 자격증명·명령/SQL 삽입·TLS 비활성화 같은 알려진 위험 패턴과, 0.0.0.0 바인딩·크기 상한 없는 요청 바디·속도 제한 없는 외부 노출이 미검토 상태로 남으면 안 된다. 노출 계층({tier})별 추가 통제는 SECURITY_NETWORK_QA_STANDARD.md의 상황별 매트릭스를 따른다"
    dev_items:
      - id: R1-D1
        description: "정적 패턴 스캐너(qa_manager/scripts/check_security_hotspots.py, check_exposure_hotspots.py)"
        test_items:
          - id: security-hotspots-guard
            category: basic
            description: "CWE 매핑된 위험 패턴(자격증명, 명령/SQL 삽입, 역직렬화, TLS, CORS)이 qa:allow 사유 없이 남아있지 않은지 확인합니다. 정적 패턴만 봅니다."
            check: "python {up}qa_manager/scripts/check_security_hotspots.py ."
            status: pending
          - id: exposure-hotspots-guard
            category: basic
            description: "CWE-1327/CWE-770/CWE-400 패턴이 qa:allow 사유 없이 남아있지 않은지 확인합니다. 정적 패턴만 보며 앞단 프록시/WAF 유무는 보지 못합니다."
            check: "python {up}qa_manager/scripts/check_exposure_hotspots.py ."
            status: pending
          - id: error-handling-hotspots-guard
            category: basic
            description: "넓은 예외를 잡고도 아무 조치를 하지 않는 핸들러(CWE-390)와 핸들러 안의 TODO/FIXME(CWE-755)가 qa:allow 사유 없이 남아있지 않은지 확인합니다. 정적 패턴만 봅니다."
            check: "python {up}qa_manager/scripts/check_error_handling_hotspots.py ."
            status: pending
          - id: operational-readiness-guard
            category: basic
            description: "브라우저로 노출되는 비밀값(CWE-540), 과한 DB 권한(CWE-250), 테스트 없는 결제·계정 코드를 확인하고, 노출 계층 T2에서는 알림·백업·복원 시험의 흔적도 요구합니다(OPERATIONS_QA_STANDARD.md). 흔적의 유무만 보며 알림 도달과 복원 성공은 사람이 시험합니다."
            check: "python {up}qa_manager/scripts/check_operational_readiness.py . --tier {tier}"
            status: pending
"""


def create(name: str, repo_root: str, qa_root: Path = QA_ROOT, desktop: Path = DESKTOP, tier: str = "T0") -> Path:
    """Write the starter checklist and return its path; refuse unsafe names, unknown repos, unknown tiers, and overwrites."""
    if not NAME.fullmatch(name):
        raise ValueError(f"invalid project name: {name!r}")
    if tier not in TIERS:
        raise ValueError(f"exposure tier must be one of {', '.join(TIERS)}: {tier!r}")
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
        TEMPLATE.format(name=name, repo_root=relative.as_posix(), up=up, tier=tier, today=date.today().isoformat()),
        encoding="utf-8",
    )
    return target


def main(argv: list[str]) -> int:
    tier = "T0"
    if "--exposure" in argv:
        index = argv.index("--exposure")
        if index + 1 >= len(argv):
            print(__doc__)
            return 2
        tier = argv[index + 1]
        argv = argv[:index] + argv[index + 2:]
    if len(argv) != 2:
        print(__doc__)
        return 2
    try:
        target = create(argv[0], argv[1], tier=tier)
    except (ValueError, FileExistsError) as error:
        print(f"FAIL: {error}")
        return 1
    print(f"CREATED {target} (exposure tier {tier})")
    print("Next (manual): add the project's real tests/guards as test_items, work through the controls the standard's matrix")
    print("lists for this tier and for each feature the project has (login, uploads, URL fetching, LLM/agent), review public-HTML")
    print("exposure and add the name to PUBLIC_PROJECTS in scripts/_checklist_lib.py, update the project counts in")
    print("README.md/ELI5.html, then run python scripts/generate_system_index.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
