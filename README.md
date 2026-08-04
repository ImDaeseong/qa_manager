# qa_manager — 검수 시스템

Standalone verification system covering every sibling project on this
machine (hermes-agents, ai_prompt, ai-workspace, ai_test/ai_test1-3, skills,
...), not a dashboard belonging to any single one of them. Each project has
its own requirements → dev items → test items, tracked as structured data
and rendered as a static webpage. `index.html` is the system-level landing
page listing every project; each project also has its own page.

qa_manager lives as a sibling folder to the projects it inspects
(`C:\Users\cs930\Desktop\qa_manager`), not nested inside any of them —
originally piloted inside hermes-agents' `qa/` folder, then moved out once
the scope grew to "manage every project," which needed a location that
doesn't privilege one project's repo over the others.

## Layout

```
qa_manager/
  index.html                      generated — system-level landing page, lists all projects
  open_qa_system.bat              regenerates everything, then opens index.html
  scripts/                        tooling only, no project-specific data
    _checklist_lib.py             shared load/run helpers; resolves each project's repo_root
    run_checklist.py              terminal report for one project
    generate_checklist_dashboard.py   writes one project's dashboard.html
    generate_system_index.py      discovers every project, writes index.html
  projects/
    hermes-agents/                one project among several — not the whole system
      checklist.yaml              requirements -> dev_items -> test_items, incl. repo_root
      dashboard.html              generated, not hand-edited
```

## Adding a project

Create `projects/<name>/checklist.yaml` following the schema and field
comments at the top of `projects/hermes-agents/checklist.yaml`. It must set
`repo_root`: that project's path relative to qa_manager's parent folder
(`C:\Users\cs930\Desktop`) — e.g. `hermes-agents`, `hermes-agents/ai_prompt`,
`ai_test1`, `skills`. Every test_item's `check` command runs with that
resolved path as its working directory. Base each test_item on something
that actually exists in that project (an existing test, lint config, CI
workflow, or guard script) — don't invent checks for tooling a project
doesn't have.

## Running

```
open_qa_system.bat                                             # regenerate everything + open in browser
python scripts\generate_system_index.py                        # regenerate all projects + index.html
python scripts\generate_checklist_dashboard.py [checklist.yaml] # regenerate one project's page only
python scripts\run_checklist.py [checklist.yaml]                # terminal report for one project
```

All of these re-run every `check` command live — the `status`/`last_verified`
fields in a project's checklist.yaml are a record of the last run, not
current truth.
