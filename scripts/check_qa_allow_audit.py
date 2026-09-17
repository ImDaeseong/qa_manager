"""Audit every `qa:allow` suppression comment in tracked source files.

check_security_hotspots.py lets a line silence a finding with a same-line
`qa:allow` comment, on the honor system that the comment carries a real
reason. Nothing was checking that honor system -- an empty or malformed
`qa:allow` would suppress a finding with no accountability at all. This
script (a) fails on any `# qa:allow`/`// qa:allow` comment that doesn't
carry a CWE ID and an actual reason, and (b) prints every accepted one on
every run, so an accumulating pile of suppressions stays visible instead of
silently growing.

Only scans actual comments (a `#`/`//` immediately before `qa:allow`), so
prose that merely explains the mechanism (this file's own docstring, a
suggestion string, a doc's example syntax) is not mistaken for a live
suppression. Files that intentionally embed qa:allow syntax as test fixture
data, or the scanner/audit scripts themselves, are excluded by name.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from check_security_hotspots import SOURCE_EXTENSIONS

REPO_ROOT = Path(__file__).resolve().parent.parent
MIN_REASON_LENGTH = 10

SELF_EXCLUDE = {
    "check_qa_allow_audit.py",
    "check_security_hotspots.py",
    "check_security_hotspots_test.py",
    "test_security_hotspots.py",
}

ATTEMPT = re.compile(r"(?:#|//)\s*qa:allow\b")
ALLOW_FORMAT = re.compile(r"(?:#|//)\s*qa:allow\s+(CWE-\d+)\s*-\s*(.+)$")


def tracked_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            capture_output=True, text=True, timeout=30, check=True,
        )
        return [root / line for line in result.stdout.splitlines() if line]
    except (subprocess.SubprocessError, OSError):
        return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


def audit(root: Path) -> tuple[list[str], list[str]]:
    """Return (valid_entries, malformed_entries), each as 'file:line: text'."""
    valid: list[str] = []
    malformed: list[str] = []
    for path in tracked_files(root):
        if path.name in SELF_EXCLUDE or path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(root).as_posix()
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not ATTEMPT.search(line):
                continue
            match = ALLOW_FORMAT.search(line)
            if not match or len(match.group(2).strip()) < MIN_REASON_LENGTH:
                malformed.append(f"{rel}:{lineno}: {line.strip()}")
            else:
                valid.append(f"{rel}:{lineno}: [{match.group(1)}] {match.group(2).strip()}")
    return valid, malformed


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO_ROOT
    valid, malformed = audit(root)

    if valid:
        print(f"qa:allow audit -- {len(valid)} acknowledged risk(s) on record:")
        for entry in valid:
            print(f"  - {entry}")
    else:
        print("qa:allow audit -- no acknowledged risks on record.")

    if malformed:
        print(f"FAIL: {len(malformed)} qa:allow comment(s) missing a CWE ID or a real reason "
              f"(need: '# qa:allow CWE-<n> - <reason of at least {MIN_REASON_LENGTH} chars>'):")
        for entry in malformed:
            print(f"  - {entry}")
        return 1

    print("PASS: every qa:allow suppression carries a CWE ID and a documented reason")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
