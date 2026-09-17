"""Static pattern scan for security/hacking/network hotspots (see SECURITY_NETWORK_QA_STANDARD.md).

Usage: python scripts/check_security_hotspots.py [path]   (default: current directory)

Scans that path's git-tracked source files for a small, high-confidence set of
patterns mapped to CWE IDs: hardcoded credentials, command/SQL injection risk,
eval/exec on external input, disabled TLS verification, cleartext http calls,
and wide-open CORS. A match on a line that also carries a `qa:allow` comment
is treated as an acknowledged, documented risk and does not fail the check.

This is pattern matching, not a full security audit: it cannot see runtime
behaviour, auth flows, or business-logic flaws. It only catches what is
literally written in the source.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".ps1", ".sh", ".bat", ".cmd",
    ".go", ".rb", ".php", ".java",
}

ALLOW_MARKER = "qa:allow"

# This scanner's own rule definitions/pinned test fixtures necessarily contain
# the literal trigger substrings they detect (e.g. the CWE-78 rule's title
# literally says "shell=True"; the CWE-295 rule's pattern literally contains
# "_create_unverified_context") -- a self-scan would always flag its own
# source as a false positive. Excluded by filename, not by qa:allow, so the
# exclusion is visible in one place instead of scattered across every
# self-matching line.
SELF_EXCLUDE = {"check_security_hotspots.py", "test_security_hotspots.py"}


class Rule:
    def __init__(self, cwe: str, title: str, suggestion: str, pattern: str) -> None:
        self.cwe = cwe
        self.title = title
        self.suggestion = suggestion
        self.regex = re.compile(pattern)


RULES = [
    Rule(
        "CWE-798", "하드코딩된 자격증명",
        "리터럴 값을 지우고 환경변수/시크릿 관리자에서 읽도록 바꾸세요.",
        r"(?i)\b[A-Z0-9_]*(?:API[_-]?KEY|SECRET|PASSWORD|TOKEN|CREDENTIAL)[A-Z0-9_]*"
        r"\s*[:=]\s*['\"](?!(?:xxx|changeme|your_|example|redacted|dummy|test|<|\$\{|\{\{))"
        r"[A-Za-z0-9/+._-]{8,}['\"]",
    ),
    Rule(
        "CWE-78", "동적 명령을 shell=True로 실행",
        "외부 입력을 셸 문자열에 이어붙이지 말고 인자 리스트 + shell=False로 바꾸거나, "
        "신뢰된 설정값만 실행됨을 qa:allow 주석으로 근거를 남기세요.",
        r"(?<!`)shell\s*=\s*True(?!`)",
    ),
    Rule(
        "CWE-89", "포맷팅으로 조립한 SQL 실행",
        "파라미터 바인딩(placeholder)을 쓰고 문자열 포맷팅으로 SQL을 조립하지 마세요.",
        r"(?:execute|executemany)\s*\(\s*(?:f['\"]|['\"].*%s.*['\"]\s*%|['\"].*\{.*\}['\"]\s*\.format)",
    ),
    Rule(
        "CWE-95", "외부 입력에 eval/exec 사용",
        "eval/exec 대신 명시적 파서나 허용 목록 기반 분기로 바꾸세요.",
        r"\b(?:eval|exec)\s*\(",
    ),
    Rule(
        "CWE-502", "안전하지 않은 역직렬화",
        "pickle 대신 json을 쓰거나 신뢰된 데이터만 역직렬화하세요. "
        "yaml.load는 Loader=yaml.SafeLoader를 지정하거나 yaml.safe_load를 쓰세요.",
        r"pickle\.loads?\s*\(|yaml\.load\s*\((?!.*SafeLoader)",
    ),
    Rule(
        "CWE-295", "TLS 인증서 검증 비활성화",
        "verify=True(기본값)를 유지하거나, 사설 CA는 인증서 번들을 지정하세요.",
        r"verify\s*=\s*False|_create_unverified_context|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0",
    ),
    Rule(
        "CWE-319", "평문 http로 외부 엔드포인트 호출",
        "https://로 바꾸세요. localhost/127.0.0.1 대상은 위험이 아니므로 이 규칙에서 제외됩니다.",
        r"['\"]http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[A-Za-z0-9.-]+",
    ),
    Rule(
        "CWE-942", "CORS 전체 허용",
        "출처를 명시적으로 허용 목록화하세요. 자격증명을 함께 쓰는 와일드카드는 특히 위험합니다.",
        r"Access-Control-Allow-Origin['\"]?\s*[:=]\s*['\"]\*|origin\s*:\s*['\"]\*['\"]",
    ),
]


def tracked_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            capture_output=True, text=True, timeout=30, check=True,
        )
        names = [line for line in result.stdout.splitlines() if line]
        return [root / name for name in names]
    except (subprocess.SubprocessError, OSError):
        return [
            p for p in root.rglob("*")
            if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts
        ]


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in tracked_files(root):
        if path.name in SELF_EXCLUDE:
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if ALLOW_MARKER in line:
                continue
            for rule in RULES:
                if rule.regex.search(line):
                    rel = path.relative_to(root)
                    findings.append(
                        f"{rel}:{lineno}: [{rule.cwe}] {rule.title} - {rule.suggestion}"
                    )
    return findings


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    findings = scan(root)
    if findings:
        print(f"FAIL: {len(findings)} unacknowledged security/network hotspot(s) found:")
        for line in findings:
            print(f"  {line}")
        print("Acknowledge an accepted risk with a same-line `# qa:allow` comment, or fix it.")
        return 1
    print("PASS: no unacknowledged security/network hotspots found (static pattern scan only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
