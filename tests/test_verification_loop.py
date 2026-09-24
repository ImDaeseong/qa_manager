"""Verify bounded retry, repair, and HOLD decisions."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import _verification_loop as loop  # noqa: E402
import run_verification_loop as runner  # noqa: E402


class VerificationLoopTests(unittest.TestCase):
    def state(self) -> dict:
        return loop.new_state("sample", "auth-e2e", "verify login lifecycle")

    def test_pass_completes_loop(self):
        state = loop.record_attempt(self.state(), "pass", "ok")
        self.assertEqual((state["status"], state["next_action"]), ("complete", "stop"))

    def test_flaky_confirmation_allows_only_one_unchanged_retry(self):
        state = loop.record_attempt(self.state(), "fail", "timeout", suspect_flaky=True)
        self.assertEqual(state["next_action"], "retry_without_change")
        state = loop.record_attempt(state, "fail", "timeout", suspect_flaky=True)
        self.assertEqual(state["next_action"], "repair_required")

    def test_same_failure_three_times_enters_hold(self):
        state = self.state()
        for _ in range(3):
            state = loop.record_attempt(state, "fail", "same assertion")
        self.assertEqual((state["status"], state["next_action"]),
                         ("hold", "human_review"))
        self.assertEqual(state["exit_reason"], "maximum_iterations_reached")

    def test_same_location_failing_after_two_edits_enters_hold(self):
        state = loop.record_attempt(self.state(), "fail", "first")
        state = loop.record_attempt(state, "fail", "second", changed_files=["src/auth.py"])
        state = loop.record_attempt(state, "fail", "third", changed_files=["src/auth.py"])
        self.assertEqual(state["exit_reason"], "same_location_failed_after_two_edits")

    def test_high_risk_change_requires_human_review(self):
        state = loop.record_attempt(self.state(), "fail", "permission boundary", high_risk=True)
        self.assertEqual((state["status"], state["exit_reason"]),
                         ("hold", "high_risk_change_requires_approval"))

    def test_passing_high_risk_change_still_requires_human_review(self):
        state = loop.record_attempt(self.state(), "pass", "ok", high_risk=True)
        self.assertEqual((state["status"], state["next_action"]),
                         ("hold", "human_review"))

    def test_state_round_trip_is_complete(self):
        state = loop.record_attempt(self.state(), "fail", "assertion")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "loop.json"
            loop.write_state(path, state)
            self.assertEqual(loop.load_state(path), json.loads(path.read_text(encoding="utf-8")))

    def test_cli_retries_one_suspected_flaky_failure_and_stops_on_pass(self):
        data = {"project": "sample", "requirements": [{"dev_items": [{"test_items": [
            {"id": "auth-e2e", "check": "unused"}
        ]}]}]}
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(runner.lib, "load", return_value=data), \
             patch.object(runner.lib, "project_root", return_value=Path(folder)), \
             patch.object(runner.lib, "run_test_item",
                          side_effect=[("fail", "timeout"), ("pass", "ok")]) as run:
            state_path = Path(folder) / "loop.json"
            result = runner.main([
                "checklist.yaml", "auth-e2e", "--state", str(state_path), "--suspect-flaky"
            ])
            state = loop.load_state(state_path)
        self.assertEqual(result, 0)
        self.assertEqual(run.call_count, 2)
        self.assertEqual([attempt["status"] for attempt in state["attempts"]], ["fail", "pass"])

    def test_cli_does_not_blindly_retry_an_ordinary_failure(self):
        data = {"project": "sample", "requirements": [{"dev_items": [{"test_items": [
            {"id": "auth-e2e", "check": "unused"}
        ]}]}]}
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(runner.lib, "load", return_value=data), \
             patch.object(runner.lib, "project_root", return_value=Path(folder)), \
             patch.object(runner.lib, "run_test_item", return_value=("fail", "assertion")) as run:
            result = runner.main([
                "checklist.yaml", "auth-e2e", "--state", str(Path(folder) / "loop.json")
            ])
        self.assertEqual(result, 1)
        self.assertEqual(run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
