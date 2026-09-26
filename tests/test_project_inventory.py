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

    def test_registered_projects_publish_documentation_entry_points(self):
        """Every registered project exposes current overview, ELI5, and design entry points."""
        for name in sorted(lib.PUBLIC_PROJECTS):
            with self.subTest(name=name):
                data = lib.load(lib.QA_ROOT / "projects" / name / "checklist.yaml")
                root = lib.project_root(data)
                readme = root / "README.md"
                eli5 = root / "ELI5.html"
                design = root / "DESIGN.md"
                self.assertTrue(readme.is_file(), f"{name}: README.md missing")
                self.assertTrue(eli5.is_file(), f"{name}: ELI5.html missing")
                self.assertTrue(design.is_file(), f"{name}: DESIGN.md missing")
                self.assertIn("DESIGN.md", readme.read_text(encoding="utf-8"))
                self.assertIn("DESIGN.md", eli5.read_text(encoding="utf-8"))
                design_text = design.read_text(encoding="utf-8")
                for heading in (
                    "## Purpose",
                    "## Stakeholders, concerns, and scenarios",
                    "## Boundaries",
                    "## Main components",
                    "## Key decisions and tradeoffs",
                    "## Verification and human review",
                    "## Evidence basis and limits",
                ):
                    self.assertIn(heading, design_text, f"{name}: missing {heading}")
                for source_marker in (
                    "IEEE 1016-2009",
                    "Kruchten",
                    "Parnas",
                    "ISO/IEC 25010:2023",
                    "NIST SSDF 1.1",
                ):
                    self.assertIn(source_marker, design_text, f"{name}: missing {source_marker}")


if __name__ == "__main__":
    unittest.main()
