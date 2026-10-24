"""Static scan for network-exposure / availability hotspots (see SECURITY_NETWORK_QA_STANDARD.md).

Usage: python scripts/check_exposure_hotspots.py [path]   (default: current directory)

Complements check_security_hotspots.py (injection/credential/TLS patterns) with the
availability side that a flood of scanner traffic exercises: a server that listens on
every interface, reads a request body with no size cap, or is exposed with no rate limit.

  CWE-1327  binds to all interfaces (0.0.0.0)
  CWE-770   request body is read but the file defines no size cap
  CWE-400   file binds to all interfaces and has no rate limiting

Acknowledge an accepted risk with a same-line `qa:allow <CWE-ID> - <reason>` comment on the
flagged line. Like its sibling this is pattern matching: it cannot see a reverse proxy, WAF,
or firewall in front of the process, and a cap-looking name does not prove the cap is enforced.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_security_hotspots import ALLOW_MARKER, SOURCE_EXTENSIONS, tracked_files  # noqa: E402

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Defines the rules by literal trigger text, so a self-scan would flag its own source.
SELF_EXCLUDE = {"check_exposure_hotspots.py", "test_exposure_hotspots.py"}

# Test code asserts on these literals (e.g. "0.0.0.0 must be rejected") but is not a server.
TEST_PATH = re.compile(r"(?i)(?:^|[\\/])(?:tests?|__tests__)[\\/]|(?:^|[\\/])(?:test_[^\\/]*|[^\\/]*_test|[^\\/]*\.test)\.[a-z]+$")

ALL_INTERFACES = re.compile(r"""(?:host|HOST|bind|BIND)\b[^\n]{0,40}['"]0\.0\.0\.0['"]|\(\s*['"]0\.0\.0\.0['"]\s*,""")
BODY_READ = re.compile(r"\brfile\.read\s*\(|\brequest\.(?:json|body|form|stream|get_json)\s*\(|\bawait\s+request\.(?:json|body|form)\b")
BODY_CAP = re.compile(
    r"(?i)\b[a-z_]*max_[a-z_]*(?:bytes|size|length|body|request|chars)[a-z_]*\b"
    r"|MAX_CONTENT_LENGTH|client_max_body_size|content.?length[^\n]{0,60}\s(?:>=?|<=?)\s"
    r"|\s(?:>=?|<=?)\s[^\n]{0,60}content.?length"
)
RATE_LIMIT = re.compile(r"(?i)rate.?limit|throttl|sliding.?window|slowapi|limit_req|too many requests|\b429\b")

HINT_BIND = "개발용이면 127.0.0.1로 바꾸세요. 공개가 목적이면 앞단 프록시/방화벽 뒤에 두고 qa:allow로 사유를 남기세요."
HINT_BODY = "Content-Length를 읽기 전에 MAX_REQUEST_BYTES 같은 상한과 비교해 413으로 거부하세요."
HINT_RATE = "사용자/IP별 요청 속도 제한을 추가하거나, 앞단 WAF/프록시가 제한함을 qa:allow 사유로 남기세요."


def scan_text(rel: str, text: str) -> list[str]:
    findings: list[str] = []
    lines = text.splitlines()
    has_cap = bool(BODY_CAP.search(text))
    has_rate = bool(RATE_LIMIT.search(text))
    body_reported = False
    for lineno, line in enumerate(lines, start=1):
        if ALLOW_MARKER in line:
            continue
        if ALL_INTERFACES.search(line):
            findings.append(f"{rel}:{lineno}: [CWE-1327] 모든 인터페이스(0.0.0.0)에 바인딩 - {HINT_BIND}")
            if not has_rate:
                findings.append(f"{rel}:{lineno}: [CWE-400] 외부 노출 서버에 속도 제한 없음 - {HINT_RATE}")
        elif BODY_READ.search(line) and not has_cap and not body_reported:
            body_reported = True  # one finding per file: the cap is a file-level property
            findings.append(f"{rel}:{lineno}: [CWE-770] 요청 바디를 읽지만 크기 상한이 없음 - {HINT_BODY}")
    return findings


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in tracked_files(root):
        if path.name in SELF_EXCLUDE or path.suffix.lower() not in SOURCE_EXTENSIONS or not path.is_file():
            continue
        if TEST_PATH.search(str(path.relative_to(root))):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        findings.extend(scan_text(str(path.relative_to(root)), text))
    return findings


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    findings = scan(root)
    if findings:
        print(f"FAIL: {len(findings)} unacknowledged exposure/availability hotspot(s) found:")
        for line in findings:
            print(f"  {line}")
        print("Acknowledge an accepted risk with a same-line `qa:allow <CWE-ID> - <reason>` comment, or fix it.")
        return 1
    print("PASS: no unacknowledged exposure/availability hotspots found (static pattern scan only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
