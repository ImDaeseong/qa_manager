"""Regression tests for scripts/check_error_handling_hotspots.py (see ERROR_BOUNDARY_QA_STANDARD.md)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_error_handling_hotspots as scanner


class ErrorHandlingScannerTests(unittest.TestCase):
    def _scan(self, filename: str, content: str) -> tuple[list[str], int]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return scanner.scan(Path(tmp))

    def test_bare_except_that_passes_is_flagged(self) -> None:
        findings, _ = self._scan("a.py", "try:\n    risky()\nexcept:\n    pass\n")
        self.assertTrue(any("CWE-390" in f for f in findings))

    def test_broad_exception_that_only_logs_is_flagged(self) -> None:
        code = "try:\n    risky()\nexcept Exception as error:\n    logger.warning('failed %s', error)\n"
        findings, _ = self._scan("a.py", code)
        self.assertTrue(any("CWE-390" in f for f in findings))

    def test_broad_exception_returning_a_constant_is_flagged(self) -> None:
        code = "def f():\n    try:\n        return risky()\n    except Exception:\n        return None\n"
        findings, _ = self._scan("a.py", code)
        self.assertTrue(any("CWE-390" in f for f in findings))

    def test_broad_tuple_containing_exception_is_flagged(self) -> None:
        findings, _ = self._scan("a.py", "try:\n    risky()\nexcept (ValueError, Exception):\n    pass\n")
        self.assertTrue(any("CWE-390" in f for f in findings))

    def test_narrow_swallow_is_counted_but_does_not_fail(self) -> None:
        findings, narrow = self._scan("a.py", "try:\n    remove()\nexcept FileNotFoundError:\n    pass\n")
        self.assertEqual(findings, [])
        self.assertEqual(narrow, 1)

    def test_handler_that_reraises_is_not_flagged(self) -> None:
        findings, _ = self._scan("a.py", "try:\n    risky()\nexcept Exception:\n    logger.error('x')\n    raise\n")
        self.assertEqual(findings, [])

    def test_handler_that_converts_to_a_fallback_value_is_not_flagged(self) -> None:
        code = "def f():\n    try:\n        return risky()\n    except Exception as error:\n        return {'ok': False, 'error': str(error)}\n"
        findings, _ = self._scan("a.py", code)
        self.assertEqual(findings, [])

    def test_cli_handler_that_reports_and_returns_a_nonzero_exit_code_is_not_flagged(self) -> None:
        code = (
            "def main():\n"
            "    try:\n"
            "        return run()\n"
            "    except Exception as exc:\n"
            "        print(f'ERROR: {exc}', file=sys.stderr)\n"
            "        return 1\n"
        )
        findings, _ = self._scan("a.py", code)
        self.assertEqual(findings, [])

    def test_returning_false_or_none_after_logging_is_still_flagged(self) -> None:
        for value in ("False", "None", "0"):
            with self.subTest(value=value):
                code = (
                    "def f():\n"
                    "    try:\n"
                    "        return risky()\n"
                    "    except Exception as exc:\n"
                    "        logger.error(exc)\n"
                    f"        return {value}\n"
                )
                findings, _ = self._scan("a.py", code)
                self.assertTrue(any("CWE-390" in f for f in findings))

    def test_error_shown_to_the_user_is_not_flagged(self) -> None:
        code = (
            "try:\n"
            "    load()\n"
            "except Exception as exc:\n"
            "    st.error(f'Could not load: {exc}')\n"
        )
        findings, _ = self._scan("a.py", code)
        self.assertEqual(findings, [])

    def test_qa_allow_on_the_except_line_acknowledges_a_broad_swallow(self) -> None:
        code = "try:\n    risky()\nexcept Exception:  # qa:allow CWE-390 - best-effort cleanup, failure only leaves a temp file\n    pass\n"
        findings, _ = self._scan("a.py", code)
        self.assertEqual(findings, [])

    def test_todo_inside_a_handler_is_flagged(self) -> None:
        code = "try:\n    risky()\nexcept ValueError as error:\n    # TODO handle this properly\n    raise RuntimeError('x') from error\n"
        findings, _ = self._scan("a.py", code)
        self.assertTrue(any("CWE-755" in f for f in findings))

    def test_todo_outside_a_handler_is_not_flagged(self) -> None:
        findings, _ = self._scan("a.py", "# TODO later\ntry:\n    risky()\nexcept ValueError:\n    raise\n")
        self.assertEqual(findings, [])

    def test_test_files_and_unparsable_files_are_skipped(self) -> None:
        findings, _ = self._scan("tests/test_a.py", "try:\n    x()\nexcept:\n    pass\n")
        self.assertEqual(findings, [])
        findings, _ = self._scan("broken.py", "def (:\n")
        self.assertEqual(findings, [])

    def test_js_empty_catch_is_flagged(self) -> None:
        findings, _ = self._scan("a.js", "try { risky(); } catch (error) {}\n")
        self.assertTrue(any("CWE-390" in f for f in findings))

    def test_js_catch_with_only_a_comment_is_flagged(self) -> None:
        findings, _ = self._scan("a.ts", "try {\n  risky();\n} catch {\n  // ignore\n}\n")
        self.assertTrue(any("CWE-390" in f for f in findings))

    def test_js_swallowing_promise_catch_is_flagged(self) -> None:
        findings, _ = self._scan("a.js", "fetchData().catch(() => {});\n")
        self.assertTrue(any("CWE-390" in f for f in findings))

    def test_js_catch_that_converts_the_failure_to_a_value_is_not_flagged(self) -> None:
        code = (
            "const stat = await fs.stat(p).catch(() => null);\n"
            "if (!stat) throw new Error('missing');\n"
        )
        findings, _ = self._scan("a.js", code)
        self.assertEqual(findings, [])

    def test_js_catch_with_a_block_comment_only_is_flagged(self) -> None:
        findings, _ = self._scan("a.js", "try { risky(); } catch (e) { /* ignore */ }\n")
        self.assertTrue(any("CWE-390" in f for f in findings))

    def test_break_only_handler_is_flagged(self) -> None:
        code = (
            "for item in items:\n"
            "    try:\n"
            "        risky(item)\n"
            "    except Exception:\n"
            "        break\n"
        )
        findings, _ = self._scan("a.py", code)
        self.assertTrue(any("CWE-390" in f for f in findings))

    def test_allow_marker_on_a_continuation_line_of_the_except_clause_counts(self) -> None:
        code = (
            "try:\n"
            "    risky()\n"
            "except (\n"
            "    OSError, Exception,  # qa:allow CWE-390 - best-effort cleanup, failure only leaves a temp file\n"
            "):\n"
            "    pass\n"
        )
        findings, _ = self._scan("a.py", code)
        self.assertEqual(findings, [])

    def test_allow_marker_on_the_first_body_line_counts(self) -> None:
        code = (
            "try:\n"
            "    risky()\n"
            "except Exception:\n"
            "    pass  # qa:allow CWE-390 - best-effort cleanup, failure only leaves a temp file\n"
        )
        findings, _ = self._scan("a.py", code)
        self.assertEqual(findings, [])

    def test_unparsable_python_is_counted_not_silently_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "broken.py").write_text("def (:\n", encoding="utf-8")
            scanner.scan(Path(tmp))
            self.assertEqual(scanner.scan.unparsable, 1)

    def test_js_catch_that_handles_the_error_is_not_flagged(self) -> None:
        findings, _ = self._scan("a.js", "try { risky(); } catch (error) { report(error); }\n")
        self.assertEqual(findings, [])

    def test_js_qa_allow_acknowledges(self) -> None:
        findings, _ = self._scan("a.js", "try { risky(); } catch (error) {} // qa:allow CWE-390 - optional telemetry, never blocks the user\n")
        self.assertEqual(findings, [])


class RegisteredProjectCoverageTests(unittest.TestCase):
    """A registered project with Python or JS/TS source must run the error-handling scan (guards a forgotten registration)."""

    def test_projects_with_source_register_the_error_handling_check(self) -> None:
        import re

        missing = []
        checked = 0
        for checklist in sorted((ROOT / "projects").glob("*/checklist.yaml")):
            text = checklist.read_text(encoding="utf-8")
            repo = re.search(r"(?m)^repo_root:\s*\"?([^\"\n]+)\"?\s*$", text)
            if not repo or not (ROOT.parent / repo.group(1).strip()).is_dir():
                continue
            checked += 1
            if scanner.scannable_files(ROOT.parent / repo.group(1).strip()) and not re.search(
                r"(?m)^\s*check:\s*\".*check_error_handling_hotspots", text
            ):
                missing.append(checklist.parent.name)
        if checked == 0:
            self.skipTest("no sibling project repositories are available to inspect")
        self.assertEqual(missing, [], f"projects with source but no error-handling check: {missing}")


class ScannerAppliesToItselfTests(unittest.TestCase):
    def test_qa_manager_scripts_have_no_unacknowledged_hotspots(self) -> None:
        findings, _ = scanner.scan(ROOT)
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
