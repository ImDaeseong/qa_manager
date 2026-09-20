"""Prove the public-file guard catches account paths without exposing them."""

import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_public_paths import check, main  # noqa: E402


class PublicPathTests(unittest.TestCase):
    def test_home_paths_are_reported_by_location_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "README.md").write_text("Local: C:/Users/example/project\n", encoding="utf-8")
            project = root / "projects" / "sample"
            project.mkdir(parents=True)
            (project / "checklist.yaml").write_text("# /home/example/project\n", encoding="utf-8")
            findings = check(root)
            self.assertCountEqual(findings, ["README.md:1", "projects/sample/checklist.yaml:1"])
            self.assertNotIn("example", str(findings))
            stderr = StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(main(root), 1)
            self.assertIn("PUBLIC_PATH:", stderr.getvalue())
            self.assertNotIn("example", stderr.getvalue())

    def test_relative_paths_are_allowed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "README.md").write_text("Use ../sample and projects/sample\n", encoding="utf-8")
            self.assertEqual(check(root), [])


if __name__ == "__main__":
    unittest.main()
