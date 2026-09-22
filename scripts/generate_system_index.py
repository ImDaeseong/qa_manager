"""Build the qa_manager verification system's landing page: index.html.

This is the system-level entry point — it is not scoped to any one project,
and it shows every project's full requirement/dev-item/test-item detail
directly on this page (not just a summary count), so nothing is hidden a
click away. It discovers every projects/<name>/checklist.yaml, regenerates
that project's own dashboard.html via generate_checklist_dashboard.generate()
(each running its checks inside its own `repo_root`, exactly once — the same
render is reused here rather than re-running every check a second time), and
lists all of them with their live detail and a link into each project's own
page. Adding a project is just dropping a new
projects/<name>/checklist.yaml in after public-project review and allowlist update.

Usage:
    python scripts/generate_system_index.py
"""

from __future__ import annotations

import sys
from datetime import date
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _checklist_lib as lib  # noqa: E402
import generate_checklist_dashboard as dash  # noqa: E402
from _style import STYLE  # noqa: E402

OUTPUT_PATH = lib.QA_ROOT / "index.html"


def discover_projects() -> list[Path]:
    projects_dir = lib.QA_ROOT / "projects"
    return sorted(projects_dir.glob("*/checklist.yaml"))


def main() -> int:
    checklist_paths = discover_projects()
    if not checklist_paths:
        print(f"No projects found under {lib.QA_ROOT / 'projects'}")
        return 1
    for checklist_path in checklist_paths:
        lib.validate_public_project(checklist_path)

    rows = []
    total_fail = 0
    total_requirements = 0
    total_test_items = 0
    ready_projects = 0
    for checklist_path in checklist_paths:
        result = dash.generate(checklist_path)  # writes that project's own dashboard.html too
        total_fail += result["fail"]
        total_requirements += result["requirements"]
        total_test_items += result["test_items"]
        overall = "pass" if result["fail"] == 0 else "fail"
        readiness = result["readiness"]
        if readiness["ready"]:
            ready_projects += 1
        readiness_pill = dash.badge("excluded" if readiness.get("excluded") else "pass" if readiness["ready"] else "hold")
        readiness_label = ("공개 출시 대상 제외" if readiness.get("excluded") else
                           "출시 검토 근거 완료" if readiness["ready"] else
                           f"출시 검토 보류({len(readiness['gaps'])}개 영역)")
        rel_link = f"projects/{checklist_path.parent.name}/dashboard.html"

        rows.append(f"""
    <details class="project {overall}" {"open" if overall == "fail" else ""}>
      <summary>
        <span>{escape(result['project'])}</span>
        {dash.badge(overall)}
        {readiness_pill} <span class="desc-inline">{escape(readiness_label)}</span>
        <span class="counts-inline">요구사항 {result['requirements']}개 · 검사항목 {result['test_items']}개 · 실패 {result['fail']}건 · <a href="{escape(rel_link)}">전체 페이지 열기 →</a></span>
      </summary>
      {dash.render_readiness(readiness)}
      {''.join(result['req_html'])}
    </details>""")
        print(
            f"{'OK  ' if overall == 'pass' else 'FAIL'} {result['project']}: "
            f"{result['requirements']} requirements, {result['fail']} failing, "
            f"{'release-review-complete' if readiness['ready'] else 'gaps: ' + ','.join(readiness['gaps'])}"
        )

    fail_projects = sum(1 for row in rows if 'class="project fail"' in row)
    pass_projects = len(checklist_paths) - fail_projects

    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>검수 시스템</title>
<style>{STYLE}</style>
</head>
<body>
<h1>검수 시스템</h1>
<p class="meta">모든 프로젝트의 요구사항 · 개발항목 · 검사항목을 한 곳에서 확인합니다. 생성시각 {date.today().isoformat()} — 각 항목은 방금 실제로 실행한 결과입니다. 프로젝트를 추가하려면 README.md 참고.</p>
<div class="stat-grid">
  <div class="stat"><div class="n">{len(checklist_paths)}</div><div class="label">프로젝트</div></div>
  <div class="stat"><div class="n">{total_requirements}</div><div class="label">요구사항</div></div>
  <div class="stat"><div class="n">{total_test_items}</div><div class="label">검사항목</div></div>
  <div class="stat"><div class="n">{pass_projects}</div><div class="label">통과한 프로젝트</div></div>
  <div class="stat fail"><div class="n">{fail_projects}</div><div class="label">실패한 프로젝트</div></div>
  <div class="stat"><div class="n">{ready_projects}</div><div class="label">출시 검토 근거 완료 프로젝트</div></div>
</div>
{''.join(rows)}
</body>
</html>
"""
    html_doc = "\n".join(line.rstrip() for line in html_doc.splitlines()) + "\n"
    lib.write_public_report(OUTPUT_PATH, html_doc)
    print(f"Wrote {OUTPUT_PATH} ({len(checklist_paths)} project(s), {total_fail} total failing)")
    return 1 if total_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
