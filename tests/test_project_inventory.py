"""Keep the reviewed public project allowlist in sync with registered checklists."""

import unittest

from scripts import _checklist_lib as lib


class ProjectInventoryTests(unittest.TestCase):
    def test_reviewed_projects_have_checklists_and_checks(self):
        expected = {
            "hermes-agents", "ai_prompt", "ai-workspace", "skills", "ai_test",
            "ai_test1", "ai_test2", "ai_agent", "qa_manager", "ai_history_dashboard",
            "llm-wiki", "career", "ebook",
        }
        actual = {path.parent.name for path in (lib.QA_ROOT / "projects").glob("*/checklist.yaml")}
        self.assertEqual(actual, expected)
        self.assertEqual(lib.PUBLIC_PROJECTS, expected)
        for name in expected:
            with self.subTest(name=name):
                data = lib.load(lib.QA_ROOT / "projects" / name / "checklist.yaml")
                self.assertEqual(data["project"], name)
                self.assertTrue(data["repo_root"])
                self.assertTrue(list(lib.iter_test_items(data)))
                self.assertTrue(all(item.get("check") for _, _, item in lib.iter_test_items(data)))


if __name__ == "__main__":
    unittest.main()
