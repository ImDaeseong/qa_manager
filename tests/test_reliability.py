"""Regression test for _checklist_lib.run_test_item()'s hang-protection behavior
(qa_manager checklist.yaml R4, tagged quality_dimension: reliability, 2026-09-20).

run_test_item()'s own docstring documents a real Windows bug it works around: with
`subprocess.run(..., shell=True, timeout=...)`, the timeout only kills the cmd.exe
wrapper, not the actual child process it launched -- the child keeps running and
holding the stdout/stderr pipes open, so `communicate()` still blocks until the child
finishes on its own (reproduced directly: a 10s sleep with a 2s timeout still took
the full 10s). The `taskkill /F /T` fix kills the whole process tree. That fix had no
test of its own before this file -- test_security.py exercises run_test_item for
argument-sanitization, but never for a command that actually hangs past the timeout.
"""

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import _checklist_lib as lib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


class RunTestItemTimeoutTests(unittest.TestCase):
    def test_hung_command_is_killed_and_reported_as_timeout_failure(self):
        # A child that sleeps far longer than the (patched, short) timeout. If the
        # process-tree kill didn't actually work, this call would block for the
        # child's full sleep duration instead of returning shortly after the timeout.
        with patch.object(lib, "CHECK_TIMEOUT_SECONDS", 1):
            start = time.monotonic()
            status, output = lib.run_test_item(
                {"check": "python -c \"import time; time.sleep(30)\""}, ROOT
            )
            elapsed = time.monotonic() - start

        self.assertEqual(status, "fail")
        self.assertIn("TIMEOUT", output)
        # Generous margin over the 1s patched timeout, but nowhere near the child's
        # own 30s sleep -- proves the child was actually killed, not just abandoned.
        self.assertLess(elapsed, 15)

    def test_command_finishing_well_within_the_timeout_is_unaffected(self):
        status, output = lib.run_test_item({"check": "python -V"}, ROOT)
        self.assertEqual(status, "pass")
        self.assertNotIn("TIMEOUT", output)


if __name__ == "__main__":
    unittest.main()
