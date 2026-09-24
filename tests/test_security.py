"""Regression tests for qa_manager's command-execution security boundary."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import _checklist_lib as lib


class SecurityBoundaryTests(unittest.TestCase):
    """Prove paths, environments, commands, and captured output stay bounded."""

    def test_project_root_rejects_escape(self) -> None:
        with self.assertRaisesRegex(ValueError, "below DESKTOP_ROOT"):
            lib.project_root({"project": "escape", "repo_root": ".."})

    def test_environment_removes_credentials(self) -> None:
        env = lib.sanitized_environment(
            {"PATH": "ok", "OPENAI_API_KEY": "secret", "GH_TOKEN": "secret"}
        )
        self.assertEqual(env, {"PATH": "ok"})

    def test_output_redacts_and_truncates(self) -> None:
        raw = "OPENAI_API_KEY=topsecret Bearer abcdefghijkl sk-abcdefghijklmnop "
        cleaned = lib.sanitize_output(raw + "x" * lib.MAX_OUTPUT_CHARS)
        self.assertNotIn("topsecret", cleaned)
        self.assertNotIn("abcdefghijklmnop", cleaned)
        self.assertTrue(cleaned.endswith("[OUTPUT_TRUNCATED]"))

    def test_command_rejects_hidden_second_line(self) -> None:
        status, output = lib.run_test_item({"check": "python -V\nwhoami"}, ROOT)
        self.assertEqual(status, "fail")
        self.assertIn("single line", output)

    def test_runner_passes_sanitized_environment(self) -> None:
        fake_process = Mock()
        fake_process.communicate.return_value = ("ok", None)
        fake_process.returncode = 0
        with patch.dict("os.environ", {"PATH": "ok", "OPENAI_API_KEY": "secret"}, clear=True):
            with patch("_checklist_lib.platform.system", return_value="Windows"), \
                    patch("_checklist_lib.subprocess.Popen", return_value=fake_process) as popen:
                status, _ = lib.run_test_item({"check": "python -V"}, ROOT)
        self.assertEqual(status, "pass")
        self.assertEqual(popen.call_args.kwargs["env"], {"PATH": "ok"})

    def test_expected_nonzero_exit_requires_its_hold_diagnostic(self) -> None:
        fake_process = Mock()
        fake_process.communicate.return_value = ("release gate: HOLD\n- HUMAN_REVIEW", None)
        fake_process.returncode = 1
        item = {
            "check": "python release_gate.py",
            "expected_exit_codes": [1],
            "required_output": ["release gate: HOLD", "- HUMAN_REVIEW"],
        }
        with patch("_checklist_lib.platform.system", return_value="Windows"), \
                patch("_checklist_lib.subprocess.Popen", return_value=fake_process):
            status, _ = lib.run_test_item(item, ROOT)
        self.assertEqual(status, "pass")

        fake_process.communicate.return_value = ("Traceback: unrelated crash", None)
        with patch("_checklist_lib.platform.system", return_value="Windows"), \
                patch("_checklist_lib.subprocess.Popen", return_value=fake_process):
            status, output = lib.run_test_item(item, ROOT)
        self.assertEqual(status, "fail")
        self.assertIn("EXPECTED OUTPUT MISSING", output)

    def test_invalid_expectation_schema_fails_before_execution(self) -> None:
        with patch("_checklist_lib.subprocess.Popen") as popen:
            status, output = lib.run_test_item(
                {"check": "python -V", "expected_exit_codes": "1"}, ROOT
            )
        self.assertEqual(status, "fail")
        self.assertIn("non-empty list of integers", output)
        popen.assert_not_called()

    def test_nonzero_exit_expectation_without_diagnostic_fails_before_execution(self) -> None:
        with patch("_checklist_lib.subprocess.Popen") as popen:
            status, output = lib.run_test_item(
                {"check": "python release_gate.py", "expected_exit_codes": [1]}, ROOT
            )
        self.assertEqual(status, "fail")
        self.assertIn("require required_output markers", output)
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
