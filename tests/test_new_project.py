"""Regression tests for scripts/new_project.py (new projects start with both scanners and an exposure tier)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import new_project
from scripts import _checklist_lib as lib

SECURITY = "python ../qa_manager/scripts/check_security_hotspots.py ."
EXPOSURE = "python ../qa_manager/scripts/check_exposure_hotspots.py ."
ERRORS = "python ../qa_manager/scripts/check_error_handling_hotspots.py ."


class NewProjectTests(unittest.TestCase):
    def _sandbox(self):
        tmp = tempfile.TemporaryDirectory()
        desktop = Path(tmp.name)
        (desktop / "qa_manager" / "projects").mkdir(parents=True)
        (desktop / "demo_app").mkdir()
        return tmp, desktop

    def test_starter_checklist_loads_and_registers_both_scanners(self) -> None:
        tmp, desktop = self._sandbox()
        with tmp:
            path = new_project.create("demo", "demo_app", desktop / "qa_manager", desktop)
            data = lib.load(path)
            self.assertEqual(data["project"], "demo")
            self.assertEqual(data["repo_root"], "demo_app")
            commands = [item["check"] for _, _, item in lib.iter_test_items(data)]
            self.assertEqual(commands, [SECURITY, EXPOSURE, ERRORS])
            for script in ("check_security_hotspots.py", "check_exposure_hotspots.py", "check_error_handling_hotspots.py"):
                self.assertTrue((ROOT / "scripts" / script).is_file())

    def test_exposure_tier_defaults_to_local_and_is_recorded(self) -> None:
        tmp, desktop = self._sandbox()
        with tmp:
            default = lib.load(new_project.create("a", "demo_app", desktop / "qa_manager", desktop))
            public = lib.load(new_project.create("b", "demo_app", desktop / "qa_manager", desktop, tier="T2"))
            self.assertEqual(default["exposure_tier"], "T0")
            self.assertEqual(public["exposure_tier"], "T2")

    def test_unknown_tier_is_refused(self) -> None:
        tmp, desktop = self._sandbox()
        with tmp:
            with self.assertRaises(ValueError):
                new_project.create("demo", "demo_app", desktop / "qa_manager", desktop, tier="T9")

    def test_nested_repo_root_gets_a_depth_aware_path_and_is_normalized(self) -> None:
        tmp, desktop = self._sandbox()
        with tmp:
            (desktop / "outer" / "inner").mkdir(parents=True)
            path = new_project.create("nested", "outer/../outer/inner", desktop / "qa_manager", desktop)
            data = lib.load(path)
            self.assertEqual(data["repo_root"], "outer/inner")
            commands = [item["check"] for _, _, item in lib.iter_test_items(data)]
            self.assertEqual(commands, [
                "python ../../qa_manager/scripts/check_security_hotspots.py .",
                "python ../../qa_manager/scripts/check_exposure_hotspots.py .",
                "python ../../qa_manager/scripts/check_error_handling_hotspots.py .",
            ])

    def test_refuses_to_overwrite_an_existing_checklist(self) -> None:
        tmp, desktop = self._sandbox()
        with tmp:
            new_project.create("demo", "demo_app", desktop / "qa_manager", desktop)
            with self.assertRaises(FileExistsError):
                new_project.create("demo", "demo_app", desktop / "qa_manager", desktop)

    def test_refuses_unknown_repo_and_path_escape_and_bad_name(self) -> None:
        tmp, desktop = self._sandbox()
        with tmp:
            for name, repo in (("demo", "missing"), ("demo", "../outside"), ("../evil", "demo_app"), ("", "demo_app")):
                with self.subTest(name=name, repo=repo):
                    with self.assertRaises(ValueError):
                        new_project.create(name, repo, desktop / "qa_manager", desktop)

    def test_starter_commands_match_what_registered_projects_already_run(self) -> None:
        registered = (ROOT / "projects" / "ai_test" / "checklist.yaml").read_text(encoding="utf-8")
        self.assertIn(EXPOSURE, registered)
        template = new_project.TEMPLATE.replace("{up}", "../")
        self.assertIn(SECURITY, template)
        self.assertIn(EXPOSURE, template)
        self.assertIn(ERRORS, template)

    def test_the_standard_documents_every_tier_the_script_accepts(self) -> None:
        standard = (ROOT / "SECURITY_NETWORK_QA_STANDARD.md").read_text(encoding="utf-8")
        for tier in new_project.TIERS:
            with self.subTest(tier=tier):
                self.assertIn(f"| {tier} ", standard)


if __name__ == "__main__":
    unittest.main()
