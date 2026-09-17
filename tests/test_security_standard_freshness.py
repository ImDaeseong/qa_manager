"""Regression tests for check_security_standard_freshness's date-comparison logic."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_security_standard_freshness import check_freshness


class FreshnessTests(unittest.TestCase):
    def test_recent_date_passes(self) -> None:
        ok, _ = check_freshness("조회일: 2026-09-01.", date(2026, 9, 18))
        self.assertTrue(ok)

    def test_date_exactly_at_limit_passes(self) -> None:
        ok, _ = check_freshness("조회일: 2025-09-18.", date(2026, 9, 18))
        self.assertTrue(ok)

    def test_date_over_limit_fails(self) -> None:
        ok, message = check_freshness("조회일: 2025-09-01.", date(2026, 9, 18))
        self.assertFalse(ok)
        self.assertIn("2025-09-01", message)

    def test_missing_marker_fails(self) -> None:
        ok, message = check_freshness("no marker here", date(2026, 9, 18))
        self.assertFalse(ok)
        self.assertIn("no '조회일", message)


if __name__ == "__main__":
    unittest.main()
