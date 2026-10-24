"""Static scan for operational-readiness gaps: browser-exposed secrets, over-privileged database access, untested core features, and (for public services) no admin alerting or backup evidence (see OPERATIONS_QA_STANDARD.md).

Usage: python scripts/check_operational_readiness.py [path] [--tier T0|T1|T2]   (default: current directory, T0)

Always checked:
  OP1  CWE-540/798  a secret that ships to the browser: a client-exposed environment variable
                    (NEXT_PUBLIC_*, VITE_*, REACT_APP_*, ...) with a secret-like name, or a real-looking key,
                    private key, or `service_role` credential in browser-facing source
  OP2  CWE-250      over-privileged database access: `GRANT ALL`, or a connection URL that logs in as
                    root/postgres/sa/admin
  OP3  (policy)     payment or account code (sign-up, login, password handling) with no test that mentions it
Required only when the project declares tier T2 (reachable from the public internet):
  OP4  NIST AU-5/SI-4  evidence that an administrator is alerted when something fails
  OP5  NIST CP-9/CP-10 evidence of automatic backups and of a documented restore test

This is evidence-of-presence, not proof of operation: an alert integration in the source does not show that an alert
arrives, and a backup script does not show that a restore works. Acknowledge an accepted finding with a same-line
`qa:allow <CWE-ID> - <reason>` comment.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_error_handling_hotspots import VENDORED  # noqa: E402
from check_exposure_hotspots import TEST_PATH, candidate_files  # noqa: E402
from check_security_hotspots import ALLOW_MARKER  # noqa: E402

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SELF_EXCLUDE = {"check_operational_readiness.py", "test_operational_readiness.py"}
TIERS = ("T0", "T1", "T2")
CODE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".html", ".htm", ".json", ".yml", ".yaml", ".toml", ".sh", ".ps1", ".bat", ".cmd", ".md", ".txt", ".env", ".sql", ".cfg", ".ini"}
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte"}
BROWSER_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".vue", ".svelte", ".html", ".htm"}

CLIENT_ENV = re.compile(
    r"\b(?:NEXT_PUBLIC|VITE|REACT_APP|EXPO_PUBLIC|NUXT_PUBLIC|PUBLIC)_[A-Z0-9_]*(?:SECRET|PRIVATE|PASSWORD|TOKEN|API_?KEY|SERVICE_?ROLE|CREDENTIAL)[A-Z0-9_]*"
)
PUBLIC_BY_DESIGN = re.compile(r"(?i)PUBLISHABLE|ANON|PUBLIC_KEY|SITE_KEY|CLIENT_ID|ANALYTICS")
KEY_FORMATS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bservice_role\b"),
)
DB_ADMIN_URL = re.compile(r"(?i)\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|mssql|sqlserver)://(?:root|postgres|sa|admin|administrator)(?::|@)")
GRANT_ALL = re.compile(r"(?i)\bGRANT\s+ALL(?:\s+PRIVILEGES)?\b")

FEATURES = {
    "payment": re.compile(r"(?i)\b(?:stripe|paypal|portone|iamport|tosspayments|kakaopay|payment_intent|checkout[._]session|billing_portal)\b"),
    "account": re.compile(r"(?i)\b(?:sign_?up|sign-up|register_user|create_user|login_required|flask_login|next-auth|nextauth|bcrypt|passlib|password_hash|reset_password|jwt\.(?:encode|decode))\b"),
}
ALERTING = re.compile(
    r"(?i)sentry_sdk|@sentry/|Sentry\.init|SMTPHandler|logging\.handlers\.HTTPHandler|hooks\.slack\.com|discord(?:app)?\.com/api/webhooks|api\.telegram\.org/bot|smtplib|pagerduty|opsgenie|alertmanager"
)
BACKUP_TOOL = re.compile(
    r"(?i)pg_dump|mysqldump|mongodump|sqlite3?[^\n]{0,60}\.backup|\.backup\(|litestream|\brestic\b|\bborg\b|rclone|wal-g|pgbackrest|aws\s+s3\s+(?:sync|cp)|\bbackup[_-]?(?:script|job|db|database)\b"
)
BACKUP_SCHEDULE = re.compile(r"(?i)\bcron:|schedule:|crontab|schtasks|systemd[^\n]{0,40}\.timer|OnCalendar=|\bcron\b")
RESTORE_DOC = re.compile(r"(?i)(?:restore|복원)[^\n]{0,120}(?:test|drill|시험|검증|확인)|(?:test|drill|시험|검증|확인)[^\n]{0,120}(?:restore|복원)")
ALERT_DOC = re.compile(r"(?i)(?:alert|알림)[^\n]{0,120}(?:test|drill|시험|확인|수신)|(?:test|drill|시험|확인)[^\n]{0,120}(?:alert|알림)")


def readable_files(root: Path) -> list[tuple[Path, str, str]]:
    """(path, relative path, text) for the project's own text files: not tests, vendored code, or this scanner."""
    files = []
    for path in candidate_files(root):
        if path.name in SELF_EXCLUDE or not path.is_file():
            continue
        name = path.name.lower()
        suffix = path.suffix.lower()
        if suffix not in CODE_SUFFIXES and not name.startswith(".env"):
            continue
        rel = str(path.relative_to(root))
        if VENDORED.search(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        files.append((path, rel, text))
    return files


def _lines(text: str):
    for number, line in enumerate(text.splitlines(), start=1):
        yield number, line


def scan(root: Path, tier: str = "T0") -> tuple[list[str], list[str]]:
    """Return (failures, information) for `root` at exposure tier `tier`."""
    if tier not in TIERS:
        raise ValueError(f"tier must be one of {TIERS}")
    failures: list[str] = []
    info: list[str] = []
    files = readable_files(root)
    non_test = [(p, rel, text) for p, rel, text in files if not TEST_PATH.search(rel)]
    tests = [(p, rel, text) for p, rel, text in files if TEST_PATH.search(rel)]

    for path, rel, text in non_test:
        suffix = path.suffix.lower()
        for number, line in _lines(text):
            if ALLOW_MARKER in line:
                continue
            for match in CLIENT_ENV.finditer(line):
                if not PUBLIC_BY_DESIGN.search(match.group(0)):
                    failures.append(f"{rel}:{number}: [OP1 CWE-540] 브라우저로 내려가는 환경변수 이름에 비밀값 표지가 있음({match.group(0)}) - 서버에서만 읽고 필요한 값만 API로 내려주세요(Next.js·Vite 문서: 이 접두사 변수는 번들에 포함됨).")
            if suffix in BROWSER_SUFFIXES:
                for pattern in KEY_FORMATS:
                    if pattern.search(line):
                        failures.append(f"{rel}:{number}: [OP1 CWE-540] 브라우저로 전달되는 코드에 키·비공개 키·service_role 자격이 있음 - 서버로 옮기세요.")
                        break
            if DB_ADMIN_URL.search(line):
                failures.append(f"{rel}:{number}: [OP2 CWE-250] DB 연결이 root/postgres/sa/admin 계정으로 되어 있음 - 작업별 최소 권한 계정을 쓰세요.")
            if GRANT_ALL.search(line):
                failures.append(f"{rel}:{number}: [OP2 CWE-250] GRANT ALL로 필요 이상의 권한을 줌 - 필요한 권한만 부여하세요.")

    for name, pattern in FEATURES.items():
        feature_files = [rel for _, rel, t in non_test if Path(rel).suffix.lower() in SOURCE_SUFFIXES and pattern.search(t)]
        if not feature_files:
            continue
        if not any(pattern.search(t) for _, _, t in tests):
            failures.append(f"{feature_files[0]}:1: [OP3 policy] {name} 관련 코드({len(feature_files)}개 파일)가 있는데 이를 다루는 테스트가 없음 - 핵심 기능은 테스트로 먼저 고정하세요.")

    corpus = "\n".join(text for _, _, text in non_test)
    if tier == "T2":
        if not ALERTING.search(corpus):
            failures.append("T2: [OP4 NIST AU-5/SI-4] 오류가 났을 때 관리자에게 알리는 연동(Sentry, SMTP·웹훅·Slack·Telegram 등)의 흔적이 없음")
        if not ALERT_DOC.search(corpus):
            failures.append("T2: [OP4 NIST AU-5] 알림이 실제로 오는지 시험한 기록(문서의 '알림 시험' 등)이 없음")
        if not BACKUP_TOOL.search(corpus):
            failures.append("T2: [OP5 NIST CP-9] 데이터·DB 자동 백업 도구나 스크립트의 흔적이 없음")
        if not BACKUP_SCHEDULE.search(corpus):
            failures.append("T2: [OP5 NIST CP-9] 백업이 일정에 따라 자동으로 도는 설정(cron, schedule, 작업 스케줄러)의 흔적이 없음")
        if not RESTORE_DOC.search(corpus):
            failures.append("T2: [OP5 NIST CP-9(1)/CP-10] 백업에서 복원을 시험한 기록이 없음")
    else:
        info.append(f"INFO: 관리자 알림(OP4)과 자동 백업·복원 시험(OP5)은 계층 T2에서만 요구합니다(현재 {tier}).")
    return failures, info


def main() -> int:
    args = sys.argv[1:]
    tier = "T0"
    if "--tier" in args:
        index = args.index("--tier")
        if index + 1 >= len(args):
            print(__doc__)
            return 2
        tier = args[index + 1]
        args = args[:index] + args[index + 2:]
    if tier not in TIERS:
        print(f"FAIL: tier must be one of {', '.join(TIERS)}: {tier!r}")
        return 2
    root = Path(args[0]).resolve() if args else Path(".").resolve()
    failures, info = scan(root, tier)
    if failures:
        print(f"FAIL: {len(failures)} unacknowledged operational-readiness gap(s) found (tier {tier}):")
        for line in failures:
            print(f"  {line}")
        print("Acknowledge an accepted risk with a same-line `qa:allow <CWE-ID> - <reason>` comment, or fix it.")
    else:
        print(f"PASS: no unacknowledged operational-readiness gaps found (tier {tier}; static evidence only)")
    for line in info:
        print(line)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
