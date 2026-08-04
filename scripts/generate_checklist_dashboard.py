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
HTML/CSS). generate_system_index.py imports `generate()` below to build every
project's page in one pass.
"""

from __future__ import annotations

import sys
from datetime import date
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _checklist_lib as lib  # noqa: E402

STATUS_LABEL = {"pass": "PASS", "fail": "FAIL", "pending": "PENDING"}


def badge(status: str) -> str:
    return f'<span class="badge {status}">{STATUS_LABEL.get(status, status.upper())}</span>'


def render_test_item(test_item: dict, cwd: Path) -> tuple[str, str]:
    live_status, output = lib.run_test_item(test_item, cwd)
    html = f"""
        <li class="test-item {live_status}">
          <div class="row">
            <code>{escape(test_item.get('id', ''))}</code>
            <span class="category">{escape(test_item.get('category', ''))}</span>
            {badge(live_status)}
          </div>
          <p class="desc">{escape(test_item.get('description', ''))}</p>
          <p class="check"><code>{escape(test_item.get('check', ''))}</code></p>
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
    dev_html = []
    statuses = []
    for dev_item in req.get("dev_items", []):
        html, status = render_dev_item(dev_item, cwd)
        dev_html.append(html)
        statuses.append(status)
    req_status = "pass" if statuses and all(s == "pass" for s in statuses) else "fail" if statuses else "pending"
    html = f"""
    <details class="requirement {req_status}" open>
      <summary>
        <code>{escape(req.get('id', ''))}</code> {badge(req_status)}
        <span class="desc-inline">{escape(req.get('description', ''))}</span>
      </summary>
      <div class="dev-items">{''.join(dev_html)}
      </div>
    </details>"""
    return html, req_status


def generate(checklist_path: Path) -> dict:
    """Regenerate dashboard.html next to `checklist_path`. Returns a summary dict."""
    data = lib.load(checklist_path)
    project = data.get("project", checklist_path.parent.name)
    output_path = checklist_path.parent / "dashboard.html"
    cwd = lib.project_root(data)

    req_html = []
    req_statuses = []
    total_test_items = sum(1 for _ in lib.iter_test_items(data))

    for req in data.get("requirements", []):
        html, status = render_requirement(req, cwd)
        req_html.append(html)
        req_statuses.append(status)

    pass_count = req_statuses.count("pass")
    fail_count = req_statuses.count("fail")
    checklist_rel = checklist_path.relative_to(lib.QA_ROOT).as_posix()

    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>검수 시스템 · {escape(project)}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; background: #fff; }}
  h1 {{ font-size: 1.4rem; }}
  a.back {{ font-size: .85rem; }}
  .meta {{ color: #666; font-size: .9rem; margin-bottom: 1.5rem; }}
  .summary {{ display: flex; gap: 1rem; margin-bottom: 1.5rem; }}
  .stat {{ border: 1px solid #ddd; border-radius: 8px; padding: .75rem 1rem; }}
  .stat .n {{ font-size: 1.6rem; font-weight: 700; }}
  .badge {{ display: inline-block; font-size: .7rem; font-weight: 700; padding: .1rem .5rem; border-radius: 4px; margin-left: .3rem; }}
  .badge.pass {{ background: #d4edda; color: #1e7e34; }}
  .badge.fail {{ background: #f8d7da; color: #a71d2a; }}
  .badge.pending {{ background: #e2e3e5; color: #555; }}
  details {{ border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: .6rem; padding: .5rem .8rem; }}
  details.requirement {{ background: #fafafa; }}
  details.dev-item {{ background: #fff; margin-top: .5rem; }}
  summary {{ cursor: pointer; font-weight: 600; }}
  .desc-inline {{ font-weight: 400; color: #444; margin-left: .4rem; }}
  ul.test-items {{ list-style: none; padding-left: 0; margin: .5rem 0 0; }}
  li.test-item {{ border-left: 3px solid #ccc; padding: .4rem .6rem; margin-bottom: .4rem; background: #fcfcfc; }}
  li.test-item.pass {{ border-left-color: #1e7e34; }}
  li.test-item.fail {{ border-left-color: #a71d2a; }}
  .row {{ display: flex; align-items: center; gap: .5rem; }}
  .category {{ font-size: .7rem; color: #888; border: 1px solid #ddd; border-radius: 4px; padding: 0 .3rem; }}
  p.desc {{ margin: .3rem 0 0; font-size: .9rem; }}
  p.check {{ margin: .2rem 0 0; font-size: .8rem; color: #555; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #1a1a1a; color: #eee; }}
    .stat {{ border-color: #444; }}
    details {{ border-color: #444; }}
    details.requirement {{ background: #222; }}
    details.dev-item {{ background: #1a1a1a; }}
    li.test-item {{ background: #222; }}
    p.check {{ color: #aaa; }}
    .meta {{ color: #aaa; }}
    .desc-inline {{ color: #ccc; }}
  }}
</style>
</head>
<body>
<p><a class="back" href="../../index.html">← 검수 시스템 전체 (모든 프로젝트)</a></p>
<h1>{escape(project)}</h1>
<p class="meta">{escape(checklist_rel)} 기반 (실행 위치: {escape(str(cwd))}), 생성시각 {date.today().isoformat()} — 각 항목은 생성 시점에 실제로 실행된 결과입니다 (기록된 status가 아님).</p>
<div class="summary">
  <div class="stat"><div class="n">{len(req_statuses)}</div>요구사항</div>
  <div class="stat"><div class="n">{total_test_items}</div>검사항목</div>
  <div class="stat"><div class="n">{pass_count}</div>통과한 요구사항</div>
  <div class="stat"><div class="n">{fail_count}</div>실패한 요구사항</div>
</div>
{''.join(req_html)}
</body>
</html>
"""
    output_path.write_text(html_doc, encoding="utf-8")
    return {
        "project": project,
        "output_path": output_path,
        "requirements": len(req_statuses),
        "test_items": total_test_items,
        "pass": pass_count,
        "fail": fail_count,
    }


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
