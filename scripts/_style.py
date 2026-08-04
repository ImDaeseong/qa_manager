"""Shared CSS for the qa_manager system's generated pages (index.html and
every project's dashboard.html). Kept in one place so both pages look
consistent and a style change doesn't need to be made twice.
"""

from __future__ import annotations

STYLE = """
  :root {
    --bg: #f6f4fb;
    --card-bg: #ffffff;
    --border: #e7e2f5;
    --text: #201c33;
    --text-muted: #6f6a85;
    --primary: #7c3aed;
    --primary-soft: #efe9fe;
    --pass-bg: #dcfce7; --pass-text: #15803d;
    --fail-bg: #fee2e2; --fail-text: #b91c1c;
    --pending-bg: #eef0f4; --pending-text: #6b7280;
    --shadow: 0 1px 2px rgba(32,28,51,.05), 0 4px 14px rgba(32,28,51,.06);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #17151f;
      --card-bg: #211e2c;
      --border: #34304a;
      --text: #f1eefb;
      --text-muted: #a9a3c2;
      --primary: #a78bfa;
      --primary-soft: #2c2540;
      --pass-bg: #113123; --pass-text: #4ade80;
      --fail-bg: #3a1414; --fail-text: #f87171;
      --pending-bg: #2a2736; --pending-text: #a9a3c2;
      --shadow: 0 1px 2px rgba(0,0,0,.3), 0 4px 16px rgba(0,0,0,.35);
    }
  }
  * { box-sizing: border-box; }
  body {
    font-family: "Segoe UI", -apple-system, sans-serif;
    max-width: 920px; margin: 0 auto; padding: 2.5rem 1.25rem 4rem;
    color: var(--text); background: var(--bg);
    line-height: 1.5;
  }
  h1 { font-size: 1.6rem; font-weight: 800; margin: .2rem 0 .3rem; letter-spacing: -.01em; }
  a { color: var(--primary); }
  a.back {
    display: inline-flex; align-items: center; gap: .3rem;
    font-size: .85rem; font-weight: 600; text-decoration: none;
    color: var(--primary); margin-bottom: .8rem;
  }
  a.back:hover { text-decoration: underline; }
  p.meta { color: var(--text-muted); font-size: .85rem; margin: 0 0 1.6rem; }
  .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: .7rem; margin-bottom: 2rem; }
  .stat {
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px;
    padding: 1rem 1.1rem; box-shadow: var(--shadow);
  }
  .stat .n { font-size: 1.7rem; font-weight: 800; color: var(--primary); }
  .stat .label { font-size: .78rem; color: var(--text-muted); margin-top: .15rem; }
  .stat.fail .n { color: var(--fail-text); }

  .pill {
    display: inline-flex; align-items: center; gap: .25rem;
    font-size: .68rem; font-weight: 700; letter-spacing: .02em;
    padding: .2rem .55rem; border-radius: 999px; margin-left: .4rem;
    text-transform: uppercase;
  }
  .pill.pass { background: var(--pass-bg); color: var(--pass-text); }
  .pill.fail { background: var(--fail-bg); color: var(--fail-text); }
  .pill.pending { background: var(--pending-bg); color: var(--pending-text); }

  details {
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px;
    margin-bottom: .65rem; padding: .7rem 1rem; box-shadow: var(--shadow);
  }
  details[open] > summary { margin-bottom: .5rem; }
  summary {
    cursor: pointer; font-weight: 700; list-style: none;
    display: flex; align-items: center; flex-wrap: wrap; gap: .3rem;
  }
  summary::-webkit-details-marker { display: none; }
  summary::before {
    content: "▸"; display: inline-block; color: var(--primary);
    transition: transform .12s ease; font-size: .8em;
  }
  details[open] > summary::before { transform: rotate(90deg); }

  details.project { border-left: 4px solid var(--primary); }
  details.project.fail { border-left-color: var(--fail-text); }
  details.requirement { background: var(--primary-soft); border-color: var(--border); }
  details.dev-item { margin-top: .5rem; }

  .desc-inline { font-weight: 400; color: var(--text-muted); margin-left: .2rem; font-size: .92rem; }
  .counts-inline { font-weight: 400; color: var(--text-muted); font-size: .78rem; margin-left: auto; }

  ul.test-items { list-style: none; padding-left: 0; margin: .5rem 0 0; }
  li.test-item {
    border-left: 3px solid var(--border); border-radius: 8px;
    padding: .5rem .7rem; margin-bottom: .4rem; background: var(--bg);
  }
  li.test-item.pass { border-left-color: var(--pass-text); }
  li.test-item.fail { border-left-color: var(--fail-text); }
  .row { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; }
  .category {
    font-size: .68rem; color: var(--text-muted); border: 1px solid var(--border);
    border-radius: 999px; padding: .05rem .5rem;
  }
  code { font-family: "Cascadia Code", Consolas, monospace; font-size: .85em; }
  p.desc { margin: .35rem 0 0; font-size: .88rem; }
  p.check { margin: .25rem 0 0; font-size: .8rem; color: var(--text-muted); }

  ul.projects { list-style: none; padding: 0; }
"""
