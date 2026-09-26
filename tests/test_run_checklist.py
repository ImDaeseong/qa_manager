"""Regression test for scripts/run_checklist.py's exit code (2026-09-26 independent review).

run_checklist.py's terminal marker treats any non-"pass" live_status as "FAIL"
text, but its exit-code logic used to only fire on the literal string "fail" --
so a test_item with a missing/empty `check` command (live_status="pending")
printed a FAIL line and a stale-status MISMATCH, yet the script's own process
exit code stayed 0. Any caller that only checks the exit code (a pre-commit
hook, a CI step, `run_checklist.py && echo ok`) would see success while the
printed report said otherwise. No test file for run_checklist.py existed
before this one.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import run_checklist  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _write_checklist(path: Path, *, with_check: bool) -> None:
    test_item_lines = [
        "          - id: T1",
        "            category: regression",
        "            description: fixture item",
    ]
    if with_check:
        test_item_lines.append('            check: "python -c \\"pass\\""')
    test_item_lines.append("            status: pass")

    path.write_text(
        "project: _run_checklist_fixture\n"
        "repo_root: qa_manager\n"
        "requirements:\n"
        "  - id: R1\n"
        "    description: fixture requirement\n"
        "    quality_dimension: reliability\n"
        "    dev_items:\n"
        "      - id: R1-D1\n"
        "        description: fixture dev item\n"
        "        test_items:\n"
        + "\n".join(test_item_lines)
        + "\n",
        encoding="utf-8",
    )


class RunChecklistExitCodeTests(unittest.TestCase):
    def test_missing_check_command_fails_the_exit_code_not_only_the_marker(self):
        fixture = ROOT / "tests" / "_tmp_run_checklist_no_check.yaml"
        _write_checklist(fixture, with_check=False)
        try:
            exit_code = run_checklist.main([str(fixture)])
        finally:
            fixture.unlink(missing_ok=True)
        self.assertEqual(
            exit_code,
            1,
            "a test_item with no check command (live_status='pending') must fail "
            "the script's exit code, matching the printed FAIL marker -- not exit 0",
        )

    def test_passing_check_command_still_exits_zero(self):
        fixture = ROOT / "tests" / "_tmp_run_checklist_with_check.yaml"
        _write_checklist(fixture, with_check=True)
        try:
            exit_code = run_checklist.main([str(fixture)])
        finally:
            fixture.unlink(missing_ok=True)
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
