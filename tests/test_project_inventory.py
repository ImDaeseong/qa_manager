"""Keep the reviewed public project allowlist in sync with registered checklists."""

import unittest

from scripts import _checklist_lib as lib


class ProjectInventoryTests(unittest.TestCase):
    def test_qa_manager_checks_do_not_reenter_the_full_suite(self):
        """Keep system generation from recursively invoking itself through its own checklist."""
        checklist = (lib.QA_ROOT / "projects" / "qa_manager" / "checklist.yaml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("unittest discover", checklist)
        self.assertIn("tests.test_security tests.test_run_checklist", checklist)
        self.assertIn("tests.test_security_hotspots", checklist)

    def test_ebook_source_delegates_leaf_products_once(self):
        """Keep leaf-product execution in the repository-local registry."""
        checklist = (lib.QA_ROOT / "projects" / "ebook_source" / "checklist.yaml").read_text(
            encoding="utf-8"
        )
        command = "python -B sample_project/qa_manager/scripts/run_registry.py --products-only"
        self.assertEqual(checklist.count(command), 1)
        self.assertIn("CHILD REGISTRY PASS", checklist)
        for product in (
            "ai_history_dashboard", "ai_knowledge_system", "idea_planner",
            "llm-wiki", "qa_manager", "source_intelligence_analyzer",
        ):
            self.assertNotIn(f"projects/{product}/checklist.yaml", checklist)

    def test_reviewed_projects_have_checklists_and_checks(self):
        expected = {
            "hermes-agents", "ai_prompt", "ai-workspace", "skills", "ai_test",
            "ai_test1", "ai_test2", "ai_agent", "qa_manager", "ai_history_dashboard",
            "llm-wiki", "career", "ebook", "ebook_source",
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

    def test_project_count_is_current_in_entry_documents(self):
        """README and ELI5 advertise the same project count as the registry."""
        count = len(lib.PUBLIC_PROJECTS)
        readme = (lib.QA_ROOT / "README.md").read_text(encoding="utf-8")
        eli5 = (lib.QA_ROOT / "ELI5.html").read_text(encoding="utf-8")
        self.assertIn(f"총 {count}개", readme)
        self.assertIn(f"{count}개 프로젝트", eli5)

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

    def test_design_docs_have_project_specific_detailed_views(self):
        """Detailed views stay evidence-backed and specific to each registered project."""
        expected_markers = {'ai-workspace': 'scripts/build_context_packet.py', 'ai_agent': 'src/agentlab/', 'ai_history_dashboard': 'scripts/regenerate.js', 'ai_prompt': 'promotion-manifest.json', 'ai_test': 'windows-port-monitor/', 'ai_test1': 'aim_music_character_app/', 'ai_test2': 'timeline.json / shot_list.md / CapCut draft', 'career': 'private evidence record (ignored local storage)', 'ebook': 'validate_manuscript.py + unit tests', 'ebook_source': 'verify_distribution.py', 'hermes-agents': 'MCP/tool permission boundary', 'llm-wiki': 'wiki-extension content script', 'qa_manager': 'verifier judgment (PASS / DETECTED / MISSED / INVALID)', 'skills': 'runtime-dependencies.lock.json'}
        detailed_sections = set()
        for name in sorted(lib.PUBLIC_PROJECTS):
            with self.subTest(name=name):
                data = lib.load(lib.QA_ROOT / "projects" / name / "checklist.yaml")
                design_text = (lib.project_root(data) / "DESIGN.md").read_text(encoding="utf-8")
                self.assertIn("## Detailed structure and views", design_text)
                self.assertIn(expected_markers[name], design_text)
                self.assertIn("ISO/IEC/IEEE 42010:2022", design_text)
                self.assertIn("SEI Views and Beyond", design_text)
                detailed = design_text.split("## Detailed structure and views", 1)[1].split(
                    "## Key decisions and tradeoffs", 1
                )[0].strip()
                self.assertGreater(len(detailed), 400, f"{name}: detailed view is too thin")
                self.assertNotIn(detailed, detailed_sections, f"{name}: duplicate detailed view")
                detailed_sections.add(detailed)


if __name__ == "__main__":
    unittest.main()
