"""Render one project's projects/<name>/checklist.yaml as a static HTML page.

This is one project's page within the qa_manager verification system, not a
standalone single-project dashboard — the system covers every project under
projects/, and this page links back to the system index (index.html, built
by generate_system_index.py). Requirements -> dev items -> test items, each
test item's `check` command run live in that project's own `repo_root` (not
read from the hand-recorded `status` field — see checklist.yaml's header
comment and run_checklist.py for why). A dev item is "pass" only if all its
test items pass; a requirement is "pass" only if all its dev items pass.

Usage:
    python scripts/generate_checklist_dashboard.py [path/to/checklist.yaml]

With no argument, uses projects/hermes-agents/checklist.yaml. Writes
dashboard.html next to the checklist.yaml it read. Open it directly in a
browser; no server or external network resource is required (self-contained
HTML/CSS). generate_system_index.py imports `render_project()` below to
embed every project's detail directly on the system index, reusing the same
live check run instead of running every check a second time.
"""

from __future__ import annotations

import sys
from datetime import date
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _checklist_lib as lib  # noqa: E402
from _style import STYLE  # noqa: E402

STATUS_LABEL = {"pass": "통과", "fail": "실패", "pending": "대기"}
CATEGORY_LABEL = {"basic": "기본검사", "full": "통합검사", "regression": "재발방지검사"}


def badge(status: str) -> str:
    return f'<span class="pill {status}">{STATUS_LABEL.get(status, status.upper())}</span>'


def render_test_item(test_item: dict, cwd: Path) -> tuple[str, str]:
    live_status, output = lib.run_test_item(test_item, cwd)
    description = test_item.get("description", "")
    desc_html = f'<p class="desc">{escape(description)}</p>' if description else ""
    category = test_item.get("category", "")
    category_label = CATEGORY_LABEL.get(category, category)
    html = f"""
        <li class="test-item {live_status}">
          <div class="row">
            <code>{escape(test_item.get('id', ''))}</code>
            <span class="category">{escape(category_label)}</span>
            {badge(live_status)}
          </div>
          {desc_html}
          <p class="check">실행 명령: <code>{escape(test_item.get('check', ''))}</code></p>
        </li>"""
    return html, live_status


def render_dev_item(dev_item: dict, cwd: Path) -> tuple[str, str]:
    item_html = []
    statuses = []
    for test_item in dev_item.get("test_items", []):
        html, status = render_test_item(test_item, cwd)
        item_html.append(html)
        statuses.append(status)
    dev_status = "pass" if statuses and all(s == "pass" for s in statuses) else "fail" if statuses else "pending"
    html = f"""
      <details class="dev-item {dev_status}" open>
        <summary>
          <code>{escape(dev_item.get('id', ''))}</code> {badge(dev_status)}
          <span class="desc-inline">{escape(dev_item.get('description', ''))}</span>
        </summary>
        <ul class="test-items">{''.join(item_html)}
        </ul>
      </details>"""
    return html, dev_status


def render_requirement(req: dict, cwd: Path) -> tuple[str, str]:
    dev_items = req.get("dev_items", [])
    dev_html = []
    statuses = []
    test_item_count = 0
    for dev_item in dev_items:
        html, status = render_dev_item(dev_item, cwd)
        dev_html.append(html)
        statuses.append(status)
        test_item_count += len(dev_item.get("test_items", []))
    req_status = "pass" if statuses and all(s == "pass" for s in statuses) else "fail" if statuses else "pending"
    coverage = f"커버리지: 개발항목 {len(dev_items)}개 · 검사항목 {test_item_count}개 연결됨" if dev_items else "커버리지: 연결된 검사항목 없음"
    coverage_class = "covered" if dev_items else "uncovered"
    html = f"""
    <details class="requirement {req_status}" open>
      <summary>
        <code>{escape(req.get('id', ''))}</code> {badge(req_status)}
        <span class="desc-inline">{escape(req.get('description', ''))}</span>
      </summary>
      <p class="coverage {coverage_class}">{escape(coverage)}</p>
      <div class="dev-items">{''.join(dev_html)}
      </div>
    </details>"""
    return html, req_status


def render_project(checklist_path: Path) -> dict:
    """Run every check in `checklist_path` live once. Returns rendered HTML + stats.

    Used both to write that project's own dashboard.html and, by
    generate_system_index.py, to embed the same detail on the system index
    without running the checks a second time.
    """
    data = lib.load(checklist_path)
    project = data.get("project", checklist_path.parent.name)
    cwd = lib.project_root(data)
    checklist_rel = checklist_path.relative_to(lib.QA_ROOT).as_posix()

    req_html = []
    req_statuses = []
    total_test_items = sum(1 for _ in lib.iter_test_items(data))

    for req in data.get("requirements", []):
        html, status = render_requirement(req, cwd)
        req_html.append(html)
        req_statuses.append(status)

    pass_count = req_statuses.count("pass")
    fail_count = req_statuses.count("fail")

    return {
        "project": project,
        "checklist_path": checklist_path,
        "checklist_rel": checklist_rel,
        "cwd": cwd,
        "req_html": req_html,
        "requirements": len(req_statuses),
        "test_items": total_test_items,
        "pass": pass_count,
        "fail": fail_count,
    }


def generate(checklist_path: Path) -> dict:
    """Run render_project() and write that project's standalone dashboard.html."""
    result = render_project(checklist_path)
    output_path = checklist_path.parent / "dashboard.html"

    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>검수 시스템 · {escape(result['project'])}</title>
<style>{STYLE}</style>
</head>
<body>
<a class="back" href="../../index.html">← 검수 시스템 전체 (모든 프로젝트)</a>
<h1>{escape(result['project'])}</h1>
<p class="meta">{escape(result['checklist_rel'])} 기반 (실행 위치: {escape(str(result['cwd']))}), 생성시각 {date.today().isoformat()} — 각 항목은 생성 시점에 실제로 실행된 결과입니다 (기록된 status가 아님).</p>
<div class="stat-grid">
  <div class="stat"><div class="n">{result['requirements']}</div><div class="label">요구사항</div></div>
  <div class="stat"><div class="n">{result['test_items']}</div><div class="label">검사항목</div></div>
  <div class="stat"><div class="n">{result['pass']}</div><div class="label">통과한 요구사항</div></div>
  <div class="stat fail"><div class="n">{result['fail']}</div><div class="label">실패한 요구사항</div></div>
</div>
{''.join(result['req_html'])}
</body>
</html>
"""
    output_path.write_text(html_doc, encoding="utf-8")
    result["output_path"] = output_path
    return result


def main(argv: list[str]) -> int:
    checklist_path = Path(argv[0]) if argv else lib.DEFAULT_CHECKLIST
    summary = generate(checklist_path)
    print(
        f"Wrote {summary['output_path']} ({summary['requirements']} requirements, "
        f"{summary['test_items']} test items, {summary['fail']} failing)"
    )
    return 1 if summary["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
