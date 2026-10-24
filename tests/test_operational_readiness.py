"""Regression tests for scripts/check_operational_readiness.py."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_operational_readiness as scanner


class OperationalReadinessTests(unittest.TestCase):
    def _scan(self, files: dict[str, str], tier: str = "T0") -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            for name, content in files.items():
                path = Path(tmp) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            return scanner.scan(Path(tmp), tier)[0]

    def test_client_exposed_secret_env_flagged(self) -> None:
        findings = self._scan({"app.ts": "const k = process.env.NEXT_PUBLIC_API_SECRET;\n"})
        self.assertTrue(any("OP1" in f for f in findings))

    def test_public_by_design_env_not_flagged(self) -> None:
        self.assertEqual(self._scan({"app.ts": "const k = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;\n"}), [])

    def test_admin_db_url_and_grant_all_flagged(self) -> None:
        findings = self._scan({"db.py": 'URL = "postgresql://postgres:pw@db/app"\n', "s.sql": "GRANT ALL ON app TO u;\n"})
        self.assertEqual(sum("OP2" in f for f in findings), 2)

    def test_untested_payment_code_flagged_and_test_clears_it(self) -> None:
        code = "import stripe\n"
        self.assertTrue(any("OP3" in f for f in self._scan({"pay.py": code})))
        self.assertEqual(self._scan({"pay.py": code, "tests/test_pay.py": "# stripe checkout\n"}), [])

    def test_qa_allow_acknowledges_finding(self) -> None:
        line = 'GRANT ALL ON app TO u;  -- qa:allow CWE-250 - local dev fixture only\n'
        self.assertEqual(self._scan({"s.sql": line}), [])

    def test_t2_requires_alerting_and_backup_but_t0_does_not(self) -> None:
        self.assertEqual(self._scan({"a.py": "x = 1\n"}, "T0"), [])
        findings = self._scan({"a.py": "x = 1\n"}, "T2")
        self.assertTrue(any("OP4" in f for f in findings))
        self.assertTrue(any("OP5" in f for f in findings))

    def _main(self, *argv: str) -> int:
        old = sys.argv
        sys.argv = ["check_operational_readiness.py", *argv]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                return scanner.main()
        finally:
            sys.argv = old

    def test_tier_equals_form_is_honored_and_bad_cli_input_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.py").write_text("x = 1\n", encoding="utf-8")
            self.assertEqual(self._main(tmp, "--tier=T2"), 1)  # T2 evidence missing -> FAIL, not a silent T0 PASS
            self.assertEqual(self._main(tmp, "--tier=T0"), 0)
            self.assertEqual(self._main(tmp, "--tier=T9"), 2)
            self.assertEqual(self._main(tmp, "--bogus"), 2)
            self.assertEqual(self._main(str(Path(tmp) / "missing")), 2)
            self.assertEqual(self._main(str(Path(tmp) / "a.py")), 2)

    def test_t2_test_record_needs_a_whole_word_not_latest(self) -> None:
        docs = {"README.md": "alert on failure; latest\ncron job pg_dump; restore of latest\nimport sentry_sdk\n"}
        findings = self._scan(docs, "T2")
        self.assertTrue(any("알림이 실제로 오는지" in f for f in findings))
        self.assertTrue(any("복원을 시험한 기록" in f for f in findings))
        real = {"README.md": "alert test: sent a test alert, received\ncron job pg_dump; restore test done\nimport sentry_sdk\n"}
        findings = self._scan(real, "T2")
        self.assertFalse(any("알림이 실제로 오는지" in f or "복원을 시험한 기록" in f for f in findings))

    def test_invalid_tier_rejected(self) -> None:
        with self.assertRaises(ValueError):
            scanner.scan(Path("."), "T9")


if __name__ == "__main__":
    unittest.main()
