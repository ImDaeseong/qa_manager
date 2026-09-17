"""Regression tests for check_qa_allow_audit's comment-format validation."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_qa_allow_audit import audit


class QaAllowAuditTests(unittest.TestCase):
    def _audit_one(self, filename: str, content: str) -> tuple[list[str], list[str]]:
        tmp = Path(tempfile.mkdtemp(prefix="qa_allow_audit_test_"))
        (tmp / filename).write_text(content, encoding="utf-8")
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        return audit(tmp)

    def test_well_formed_allow_is_valid(self) -> None:
        valid, malformed = self._audit_one(
            "app.py", "x = 1  # qa:allow CWE-78 - trusted constant, not external input\n",
        )
        self.assertEqual(malformed, [])
        self.assertEqual(len(valid), 1)

    def test_missing_reason_is_malformed(self) -> None:
        valid, malformed = self._audit_one("app.py", "x = 1  # qa:allow\n")
        self.assertEqual(valid, [])
        self.assertEqual(len(malformed), 1)

    def test_missing_cwe_id_is_malformed(self) -> None:
        valid, malformed = self._audit_one(
            "app.py", "x = 1  # qa:allow because it is fine trust me\n",
        )
        self.assertEqual(valid, [])
        self.assertEqual(len(malformed), 1)

    def test_reason_too_short_is_malformed(self) -> None:
        valid, malformed = self._audit_one("app.py", "x = 1  # qa:allow CWE-78 - ok\n")
        self.assertEqual(valid, [])
        self.assertEqual(len(malformed), 1)

    def test_prose_mention_without_comment_prefix_ignored(self) -> None:
        valid, malformed = self._audit_one(
            "notes.py",
            '"""Explains that an accepted risk needs a qa:allow CWE-78 comment."""\n',
        )
        self.assertEqual(valid, [])
        self.assertEqual(malformed, [])

    def test_own_test_fixture_file_self_excluded(self) -> None:
        # Regression: the audit script's own test file embeds malformed
        # qa:allow strings as CASES data, not real suppressions -- forgetting
        # to add "test_qa_allow_audit.py" to SELF_EXCLUDE made this guard
        # fail on itself the moment it was committed (found live 2026-09-18,
        # the same defect class as check_security_hotspots.py's self-scan bug).
        valid, malformed = self._audit_one(
            "test_qa_allow_audit.py", "x = 1  # qa:allow\n",
        )
        self.assertEqual(valid, [])
        self.assertEqual(malformed, [])

    def test_non_source_extension_ignored(self) -> None:
        valid, malformed = self._audit_one("NOTES.md", "# qa:allow bad no reason\n")
        self.assertEqual(valid, [])
        self.assertEqual(malformed, [])


if __name__ == "__main__":
    unittest.main()
