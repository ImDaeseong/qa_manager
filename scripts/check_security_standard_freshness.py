"""Fail if SECURITY_NETWORK_QA_STANDARD.md's cited CWE/OWASP mapping hasn't been
re-checked against the current CWE Top 25 / OWASP Top 10 in over a year.

The CWE Top 25 is republished annually (see the document's own 근거 section).
A one-time citation goes stale silently with no other signal -- this makes
that staleness a concrete, dated, checkable failure instead of a prose
reminder nobody re-reads (AGENTS.md Currency Rule).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "SECURITY_NETWORK_QA_STANDARD.md"
MAX_AGE_DAYS = 365


def check_freshness(text: str, today: date) -> tuple[bool, str]:
    """Return (ok, message) for the doc's 조회일 marker as of `today`."""
    match = re.search(r"조회일:\s*(\d{4})-(\d{2})-(\d{2})", text)
    if not match:
        return False, "no '조회일: YYYY-MM-DD' marker to check freshness against"

    checked = date(*(int(part) for part in match.groups()))
    age_days = (today - checked).days
    if age_days > MAX_AGE_DAYS:
        return False, (
            f"last checked against CWE Top 25/OWASP Top 10 on {checked.isoformat()} "
            f"({age_days} days ago, over the {MAX_AGE_DAYS}-day limit). "
            "Re-verify the current-year lists (WebSearch) and update the 조회일 marker."
        )
    return True, f"checked against current standards {age_days} day(s) ago"


def main() -> int:
    if not DOC.is_file():
        print(f"FAIL: {DOC.name} not found")
        return 1

    ok, message = check_freshness(DOC.read_text(encoding="utf-8"), date.today())
    print(f"{'PASS' if ok else 'FAIL'}: {DOC.name} {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
