"""Regression tests for scripts/check_exposure_hotspots.py (see SECURITY_NETWORK_QA_STANDARD.md)."""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_exposure_hotspots as scanner


class ExposureHotspotScannerTests(unittest.TestCase):
    def _scan(self, filename: str, content: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return scanner.scan(Path(tmp))

    def test_detects_all_interfaces_bind_and_missing_rate_limit(self) -> None:
        findings = self._scan("app.py", 'uvicorn.run(app, host="0.0.0.0", port=8000)\n')
        self.assertTrue(any("CWE-1327" in f for f in findings))
        self.assertTrue(any("CWE-400" in f for f in findings))

    def test_detects_tuple_style_bind(self) -> None:
        findings = self._scan("srv.py", 'server = HTTPServer(("0.0.0.0", 8080), Handler)\n')
        self.assertTrue(any("CWE-1327" in f for f in findings))

    def test_loopback_bind_not_flagged(self) -> None:
        self.assertEqual(self._scan("app.py", 'uvicorn.run(app, host="127.0.0.1", port=8000)\n'), [])

    def test_rate_limit_present_suppresses_only_cwe_400(self) -> None:
        findings = self._scan("app.py", 'limiter = SlidingWindowLimiter(30)\nrun(host="0.0.0.0")\n')
        self.assertTrue(any("CWE-1327" in f for f in findings))
        self.assertFalse(any("CWE-400" in f for f in findings))

    def test_detects_uncapped_body_read_once_per_file(self) -> None:
        body = "a = self.rfile.read(n)\nb = self.rfile.read(m)\n"
        findings = self._scan("web.py", body)
        self.assertEqual(len([f for f in findings if "CWE-770" in f]), 1)

    def test_body_cap_constant_suppresses_cwe_770(self) -> None:
        body = "MAX_REQUEST_BYTES = 20_000\nraw = self.rfile.read(n)\n"
        self.assertEqual(self._scan("web.py", body), [])

    def test_unrelated_max_names_do_not_mask_a_missing_body_cap(self) -> None:
        body = "MAX_OUTPUT_CHARS = 4000\nMAX_WORKERS = 4\nmax_length = 10\nraw = self.rfile.read(n)\n"
        self.assertTrue(any("CWE-770" in f for f in self._scan("web.py", body)))

    def test_upload_and_content_named_caps_count(self) -> None:
        for name in ("MAX_UPLOAD_BYTES", "MAX_CONTENT_LENGTH", "MAX_BODY", "max_request_size"):
            with self.subTest(name=name):
                self.assertEqual(self._scan("web.py", f"{name} = 1\nraw = self.rfile.read(n)\n"), [])

    def test_content_length_validator_call_counts_as_cap(self) -> None:
        body = "validate_content_length(length, POLICY)\nraw = self.rfile.read(length)\n"
        self.assertEqual(self._scan("web.py", body), [])

    def test_content_length_comparison_counts_as_cap(self) -> None:
        body = "if int(self.headers['Content-Length']) > LIMIT:\n    return\nraw = self.rfile.read(n)\n"
        self.assertEqual(self._scan("web.py", body), [])

    def test_arrow_after_content_length_is_not_a_cap(self) -> None:
        body = "const n = headers['content-length'] => 0;\nraw = self.rfile.read(n)\n"
        self.assertTrue(any("CWE-770" in f for f in self._scan("web.py", body)))

    def test_detects_framework_body_read(self) -> None:
        findings = self._scan("route.ts", "const data = await request.json();\n")
        self.assertTrue(any("CWE-770" in f for f in findings))

    def test_qa_allow_on_flagged_line_acknowledges_risk(self) -> None:
        line = 'run(host="0.0.0.0")  # qa:allow CWE-1327 - behind reverse proxy and firewall\n'
        self.assertEqual(self._scan("app.py", line), [])

    def test_untracked_server_file_in_a_git_repo_is_scanned(self) -> None:
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            (Path(tmp) / "new_server.py").write_text('run(host="0.0.0.0")' + chr(10), encoding="utf-8")
            self.assertTrue(any("CWE-1327" in f for f in scanner.scan(Path(tmp))))

    def test_gitignored_file_is_not_scanned(self) -> None:
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            (Path(tmp) / ".gitignore").write_text("scratch.py" + chr(10), encoding="utf-8")
            (Path(tmp) / "scratch.py").write_text('run(host="0.0.0.0")' + chr(10), encoding="utf-8")
            self.assertEqual(scanner.scan(Path(tmp)), [])

    def test_test_files_are_skipped(self) -> None:
        self.assertEqual(self._scan("tests/test_cfg.py", 'assert reject(host="0.0.0.0")\n'), [])
        self.assertEqual(self._scan("test_cfg.py", 'assert reject(host="0.0.0.0")\n'), [])

    def test_non_test_file_with_test_substring_still_scanned(self) -> None:
        findings = self._scan("contest.py", 'run(host="0.0.0.0")\n')
        self.assertTrue(any("CWE-1327" in f for f in findings))


SERVER_CODE = re.compile(
    r"http\.server|HTTPServer|uvicorn\.run|FastAPI\(|Flask\(|express\(\)|\.createServer\(|app\.listen\(|NextRequest|socketserver"
)
DESKTOP = ROOT.parent


class RegisteredProjectCoverageTests(unittest.TestCase):
    """A registered project that ships server code must run the exposure scan (guards a forgotten registration)."""

    def test_projects_with_server_code_register_the_exposure_check(self) -> None:
        missing = []
        checked = 0
        for checklist in sorted((ROOT / "projects").glob("*/checklist.yaml")):
            text = checklist.read_text(encoding="utf-8")
            repo = re.search(r"(?m)^repo_root:\s*(\S+)", text)
            if not repo or not (DESKTOP / repo.group(1)).is_dir():
                continue
            root = DESKTOP / repo.group(1)
            checked += 1
            has_server = False
            for path in scanner.tracked_files(root):
                rel = str(path.relative_to(root))
                if path.suffix.lower() not in scanner.SOURCE_EXTENSIONS or scanner.TEST_PATH.search(rel):
                    continue
                if path.name in scanner.SELF_EXCLUDE or not path.is_file():
                    continue
                if SERVER_CODE.search(path.read_text(encoding="utf-8", errors="replace")):
                    has_server = True
                    break
            if has_server and not re.search(r"(?m)^\s*check:\s*\".*check_exposure_hotspots", text):
                missing.append(checklist.parent.name)
        if checked == 0:
            self.skipTest("no sibling project repositories are available to inspect")
        self.assertEqual(missing, [], f"projects with server code but no exposure check: {missing}")


if __name__ == "__main__":
    unittest.main()
