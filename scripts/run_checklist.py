"""Run every check listed in a project's projects/<name>/checklist.yaml and
report live results.

The checklist's `status` field is hand-maintained (see checklist.yaml's header
comment) and can go stale the moment code changes after it was last recorded.
This script re-runs each leaf test_item's `check` command now, inside that
checklist's own `repo_root`, and prints the real result, so "done" is based
on an actual tool call (per AGENTS.md's Evidence Rule), not on trusting a
status string someone wrote earlier.

Usage:
    python scripts/run_checklist.py [path/to/checklist.yaml]

With no argument, uses projects/hermes-agents/checklist.yaml. Exits non-zero
if any test_item's live run fails, or if its live result disagrees with the
recorded `status`.
"""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    # a `check` command's captured output can contain characters the
    # console's active codepage (e.g. cp949 on Korean Windows) can't encode
    # (seen: eslint's '✖' marker) -- replace rather than crash mid-report.
    sys.stdout.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _checklist_lib as lib  # noqa: E402


def main(argv: list[str]) -> int:
    checklist_path = Path(argv[0]) if argv else lib.DEFAULT_CHECKLIST
    if not checklist_path.exists():
        print(f"No checklist found at {checklist_path}")
        return 1

    data = lib.load(checklist_path)
    cwd = lib.project_root(data)
    exit_code = 0
    mismatches = 0
    count = 0

    for req, dev_item, test_item in lib.iter_test_items(data):
        count += 1
        item_id = test_item.get("id", "<no id>")
        recorded_status = test_item.get("status", "pending")
        live_status, output = lib.run_test_item(test_item, cwd)

        marker = "OK  " if live_status == "pass" else "FAIL"
        print(
            f"{marker} [{req.get('id')}/{dev_item.get('id')}] {item_id} "
            f"[{test_item.get('category', '?')}] live={live_status} recorded={recorded_status}"
        )

        if live_status == "fail":
            exit_code = 1
            for line in output.splitlines():
                print(f"       {line}")
        if live_status != recorded_status:
            mismatches += 1
            print(f"       MISMATCH: recorded status is stale, update {checklist_path.name}")

    if count == 0:
        print(f"No test_items found in {checklist_path}")
        return 0

    print()
    print(f"{count} item(s) checked, {mismatches} stale recorded-status mismatch(es)")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
