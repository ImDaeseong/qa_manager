"""Keep CI actions on reviewed source commits instead of movable tags."""

import re
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "validate.yml"


class WorkflowPinTests(unittest.TestCase):
    def test_external_actions_use_full_commit_shas(self):
        uses = re.findall(r"^\s*- uses:\s*(\S+)", WORKFLOW.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertCountEqual([action.split("@")[0] for action in uses],
                              ["actions/checkout", "actions/setup-python"])
        for action in uses:
            with self.subTest(action=action):
                self.assertRegex(action, r"^actions/(?:checkout|setup-python)@[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
