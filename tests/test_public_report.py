"""Exercise public-report safety and the complete checklist-to-HTML path."""

import sys
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import _checklist_lib as lib  # noqa: E402
import generate_system_index as system  # noqa: E402
import generate_checklist_dashboard as dashboard  # noqa: E402


class PublicReportTests(unittest.TestCase):
    def test_private_content_is_rejected_without_replacing_existing_report(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "index.html"
            target.write_text("previous complete report", encoding="utf-8")
            for private in (r"C:\Users\example\project", "/home/example/project",
                            "Bearer abcdefghijklmnopqrstuvwxyz"):
                with self.subTest(private=private):
                    with self.assertRaisesRegex(ValueError, "PUBLIC_REPORT"):
                        lib.write_public_report(target, private)
                    self.assertEqual(target.read_text(encoding="utf-8"),
                                     "previous complete report")
            self.assertEqual(list(Path(folder).iterdir()), [target])

    def test_replace_failure_preserves_previous_report_and_removes_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "index.html"
            target.write_text("previous complete report", encoding="utf-8")
            with patch.object(lib.os, "replace", side_effect=OSError("replacement failed")):
                with self.assertRaisesRegex(OSError, "replacement failed"):
                    lib.write_public_report(target, "new complete report")
            self.assertEqual(target.read_text(encoding="utf-8"),
                             "previous complete report")
            self.assertEqual(list(Path(folder).iterdir()), [target])

    def test_checklist_to_dashboard_and_index_uses_live_result(self):
        with tempfile.TemporaryDirectory() as folder:
            qa_root = Path(folder) / "qa_manager"
            qa_root.mkdir()
            project = qa_root / "projects" / "sample"
            project.mkdir(parents=True)
            repo = Path(folder) / "sample"
            repo.mkdir()
            checklist = project / "checklist.yaml"
            with patch.object(lib, "QA_ROOT", qa_root), \
                 patch.object(lib, "DESKTOP_ROOT", Path(folder)), \
                 patch.object(system, "OUTPUT_PATH", qa_root / "index.html"):
                for code, expected in (("0", 0), ("1", 1)):
                    checklist.write_text(
                        "project: sample\nrepo_root: sample\nrequirements:\n"
                        "  - id: R1\n    quality_dimension: functional_suitability\n"
                        "    dev_items:\n      - id: D1\n        test_items:\n"
                        f"          - id: T1\n            check: 'python -c \"exit({code})\"'\n"
                        "            status: pass\n", encoding="utf-8")
                    self.assertEqual(system.main(), expected)
                    for report in (qa_root / "index.html", project / "dashboard.html"):
                        html = report.read_text(encoding="utf-8")
                        self.assertIn("출시 검토 보류", html)
                        self.assertIn(f'class="requirement {"fail" if expected else "pass"}"',
                                      html)
                    self.assertIn("class=\"project fail\"" if expected else
                                  "class=\"project pass\"",
                                  (qa_root / "index.html").read_text(encoding="utf-8"))

    def test_relative_checklist_path_from_readme_runs(self):
        with tempfile.TemporaryDirectory() as folder:
            qa_root = Path(folder) / "qa_manager"
            checklist = qa_root / "projects" / "sample" / "checklist.yaml"
            checklist.parent.mkdir(parents=True)
            repo = Path(folder) / "sample"
            repo.mkdir()
            checklist.write_text("project: sample\nrepo_root: sample\nrequirements: []\n",
                                 encoding="utf-8")
            previous = Path.cwd()
            try:
                os.chdir(qa_root)
                with patch.object(lib, "QA_ROOT", qa_root), \
                     patch.object(lib, "DESKTOP_ROOT", Path(folder)):
                    result = dashboard.generate(Path("projects/sample/checklist.yaml"))
            finally:
                os.chdir(previous)
            self.assertEqual(result["project"], "sample")
            self.assertTrue((checklist.parent / "dashboard.html").is_file())


if __name__ == "__main__":
    unittest.main()
