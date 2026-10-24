"""Regression tests for scripts/new_project.py (new projects start with the exposure check registered)."""

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


class NewProjectTests(unittest.TestCase):
    def _sandbox(self):
        tmp = tempfile.TemporaryDirectory()
        desktop = Path(tmp.name)
        (desktop / "qa_manager" / "projects").mkdir(parents=True)
        (desktop / "demo_app").mkdir()
        return tmp, desktop

    def test_starter_checklist_loads_and_registers_the_exposure_check(self) -> None:
        tmp, desktop = self._sandbox()
        with tmp:
            path = new_project.create("demo", "demo_app", desktop / "qa_manager", desktop)
            data = lib.load(path)
            self.assertEqual(data["project"], "demo")
            self.assertEqual(data["repo_root"], "demo_app")
            commands = [item["check"] for _, _, item in lib.iter_test_items(data)]
            self.assertEqual(commands, ["python ../qa_manager/scripts/check_exposure_hotspots.py ."])
            self.assertTrue((ROOT / "scripts" / "check_exposure_hotspots.py").is_file())

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

    def test_real_registered_checklists_stay_loadable_with_the_same_template_check(self) -> None:
        """The starter's command string matches what the registered projects already run."""
        registered = (ROOT / "projects" / "ai_test" / "checklist.yaml").read_text(encoding="utf-8")
        self.assertIn("python ../qa_manager/scripts/check_exposure_hotspots.py .", registered)
        self.assertIn("python ../qa_manager/scripts/check_exposure_hotspots.py .", new_project.TEMPLATE)


if __name__ == "__main__":
    unittest.main()
