"""Regression tests for scripts/check_security_hotspots.py (see SECURITY_NETWORK_QA_STANDARD.md)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_security_hotspots as scanner


class SecurityHotspotScannerTests(unittest.TestCase):
    def _scan_one(self, tmp_path: Path, filename: str, content: str) -> list[str]:
        (tmp_path / filename).write_text(content, encoding="utf-8")
        return scanner.scan(tmp_path)

    def test_detects_hardcoded_api_key(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "app.py",
            'OPENAI_API_KEY = "sk-realvaluenotplaceholder123456"\n',
        )
        self.assertTrue(any("CWE-798" in f for f in findings))

    def test_placeholder_credential_not_flagged(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "app.py",
            'OPENAI_API_KEY = "your_key_here"\n',
        )
        self.assertEqual(findings, [])

    def test_detects_command_injection_shell_true(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "run.py",
            "subprocess.Popen(user_input, shell=True)\n",
        )
        self.assertTrue(any("CWE-78" in f for f in findings))

    def test_detects_pickle_deserialization(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "cache.py",
            "obj = pickle.loads(payload)\n",
        )
        self.assertTrue(any("CWE-502" in f for f in findings))

    def test_detects_unsafe_yaml_load(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "config.py",
            "data = yaml.load(stream)\n",
        )
        self.assertTrue(any("CWE-502" in f for f in findings))

    def test_yaml_safe_load_not_flagged(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "config.py",
            "data = yaml.safe_load(stream)\n",
        )
        self.assertEqual(findings, [])

    def test_yaml_load_with_safeloader_not_flagged(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "config.py",
            "data = yaml.load(stream, Loader=yaml.SafeLoader)\n",
        )
        self.assertEqual(findings, [])

    def test_backtick_reference_in_prose_not_flagged(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "notes.py",
            "# Explains why `shell=True` is required here for the taskkill workaround.\n",
        )
        self.assertEqual(findings, [])

    def test_detects_disabled_tls_verification(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "client.py",
            "requests.get(url, verify=False)\n",
        )
        self.assertTrue(any("CWE-295" in f for f in findings))

    def test_detects_cleartext_external_http(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "client.py",
            'BASE_URL = "http://api.example.com/v1"\n',
        )
        self.assertTrue(any("CWE-319" in f for f in findings))

    def test_localhost_http_not_flagged(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "client.py",
            'BASE_URL = "http://localhost:8000"\n',
        )
        self.assertEqual(findings, [])

    def test_qa_allow_comment_suppresses_finding(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "run.py",
            "subprocess.Popen(cmd, shell=True)  # qa:allow CWE-78 - cmd is a fixed constant\n",
        )
        self.assertEqual(findings, [])

    def test_non_source_extension_ignored(self) -> None:
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "notes.txt",
            'API_KEY = "sk-realvaluenotplaceholder123456"\n',
        )
        self.assertEqual(findings, [])

    def test_scanner_self_excludes_own_rule_definitions(self) -> None:
        # Regression: the scanner's own filename must be excluded, or its rule
        # titles/patterns (which literally contain "shell=True" etc.) flag
        # themselves as soon as the file is git-tracked -- found live in
        # qa_manager's own committed copy on 2026-09-18.
        findings = self._scan_one(
            Path(self._make_tmp_dir()), "check_security_hotspots.py",
            "subprocess.Popen(user_input, shell=True)\n",
        )
        self.assertEqual(findings, [])

    _tmp_dirs: list[str] = []

    def _make_tmp_dir(self) -> str:
        import tempfile

        d = tempfile.mkdtemp(prefix="qa_hotspot_test_")
        self._tmp_dirs.append(d)
        self.addCleanup(self._cleanup, d)
        return d

    @staticmethod
    def _cleanup(d: str) -> None:
        import shutil

        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
