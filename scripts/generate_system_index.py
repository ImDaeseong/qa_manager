"""Build the qa_manager verification system's landing page: index.html.

This is the system-level entry point — it is not scoped to any one project.
It discovers every projects/<name>/checklist.yaml, regenerates that project's
own dashboard.html via generate_checklist_dashboard.generate() (each running
its checks inside its own `repo_root`), and lists all of them here with a
live pass/fail summary and a link into each. Adding a project is just
dropping a new projects/<name>/checklist.yaml in — no change needed here.

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

OUTPUT_PATH = lib.QA_ROOT / "index.html"


def discover_projects() -> list[Path]:
    projects_dir = lib.QA_ROOT / "projects"
    return sorted(projects_dir.glob("*/checklist.yaml"))


def main() -> int:
    checklist_paths = discover_projects()
    if not checklist_paths:
        print(f"No projects found under {lib.QA_ROOT / 'projects'}")
        return 1

    rows = []
    total_fail = 0
    for checklist_path in checklist_paths:
        summary = dash.generate(checklist_path)
        total_fail += summary["fail"]
        overall = "pass" if summary["fail"] == 0 else "fail"
        rel_link = f"projects/{checklist_path.parent.name}/dashboard.html"
        rows.append(f"""
    <li class="project {overall}">
      <a href="{escape(rel_link)}">
        <span class="name">{escape(summary['project'])}</span>
        {dash.badge(overall)}
      </a>
      <span class="counts">요구사항 {summary['requirements']}개 · 검사항목 {summary['test_items']}개 · 실패 {summary['fail']}건</span>
    </li>""")
        print(
            f"{'OK  ' if overall == 'pass' else 'FAIL'} {summary['project']}: "
            f"{summary['requirements']} requirements, {summary['fail']} failing"
        )

    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>검수 시스템</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; background: #fff; }}
  h1 {{ font-size: 1.5rem; }}
  .meta {{ color: #666; font-size: .9rem; margin-bottom: 1.5rem; }}
  ul.projects {{ list-style: none; padding: 0; }}
  li.project {{ border: 1px solid #e0e0e0; border-radius: 8px; padding: .8rem 1rem; margin-bottom: .6rem; }}
  li.project a {{ text-decoration: none; color: inherit; font-weight: 600; font-size: 1.05rem; }}
  .counts {{ display: block; font-size: .8rem; color: #666; margin-top: .3rem; }}
  .badge {{ display: inline-block; font-size: .7rem; font-weight: 700; padding: .1rem .5rem; border-radius: 4px; margin-left: .3rem; }}
  .badge.pass {{ background: #d4edda; color: #1e7e34; }}
  .badge.fail {{ background: #f8d7da; color: #a71d2a; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #1a1a1a; color: #eee; }}
    li.project {{ border-color: #444; }}
    .counts {{ color: #aaa; }}
    .meta {{ color: #aaa; }}
  }}
</style>
</head>
<body>
<h1>검수 시스템</h1>
<p class="meta">모든 프로젝트의 요구사항 · 개발항목 · 검사항목을 한 곳에서 확인합니다. 생성시각 {date.today().isoformat()}. 프로젝트를 추가하려면 README.md 참고.</p>
<ul class="projects">{''.join(rows)}
</ul>
</body>
</html>
"""
    OUTPUT_PATH.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({len(checklist_paths)} project(s), {total_fail} total failing)")
    return 1 if total_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
