"""Catch local account paths in files intended for public distribution."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE_PATH = re.compile(r"(?i)(?:[A-Z]:[\\/]Users[\\/]|/(?:Users|home)/)[^\\/\s<>]+")


def check(root: Path = ROOT) -> list[str]:
    """Return locations of user-home paths in public docs, checklists, and reports."""
    paths = [root / "README.md", *root.glob("*.md"), *root.glob("projects/*/*.md"),
             *root.glob("projects/*/checklist.yaml"), root / "index.html",
             *root.glob("projects/*/dashboard.html")]
    findings = []
    for path in sorted(set(paths)):
        if not path.is_file():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if PRIVATE_PATH.search(line):
                findings.append(f"{path.relative_to(root).as_posix()}:{number}")
    return findings


def main(root: Path = ROOT) -> int:
    """Report path locations without printing the private path itself."""
    findings = check(root)
    if findings:
        print("PUBLIC_PATH: local user-home path in " + ", ".join(findings), file=sys.stderr)
        return 1
    print("PASS: no local user-home paths in public docs and reports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
