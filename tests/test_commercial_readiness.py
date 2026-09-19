"""Tests for _checklist_lib.commercial_readiness() — the commercial-release
readiness rollup added 2026-09-20 (AGENTS.md Commercial-Grade Baseline)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import _checklist_lib as lib  # noqa: E402


def _project(requirements):
    return {"project": "test-project", "requirements": requirements}


class CommercialReadinessTests(unittest.TestCase):
    def test_no_requirements_tagged_reports_all_dimensions_missing(self):
        data = _project([{"id": "R1", "description": "..."}])
        result = lib.commercial_readiness(data, {"R1": "pass"})
        self.assertFalse(result["ready"])
        self.assertEqual(len(result["gaps"]), len(lib.COMMERCIAL_DIMENSIONS))
        for info in result["dimensions"].values():
            self.assertEqual(info["status"], "missing")

    def test_all_dimensions_tagged_and_passing_still_needs_release_review(self):
        requirements = [
            {"id": f"R{i}", "quality_dimension": dim}
            for i, dim in enumerate(lib.COMMERCIAL_DIMENSIONS, start=1)
        ]
        statuses = {req["id"]: "pass" for req in requirements}
        result = lib.commercial_readiness(_project(requirements), statuses)
        self.assertFalse(result["ready"])
        self.assertTrue(result["approval_missing"])
        for info in result["dimensions"].values():
            self.assertEqual(info["status"], "pending_review")

    def test_every_area_needs_evidence_and_human_approval(self):
        requirements = [{"id": "R1", "quality_dimension": "security"}]
        data = _project(requirements)
        data["release_review"] = {
            "release": "1.0", "audience": "public", "distribution": "web", "jurisdictions": ["KR"],
            "areas": {key: {"decision": "pass", "evidence": "review.md"}
                      for key in lib.COMMERCIAL_DIMENSIONS},
            "approval": {"reviewer": "owner", "date": "2026-09-20", "evidence": "decision.md"},
        }
        result = lib.commercial_readiness(data, {"R1": "pass"})
        self.assertTrue(result["ready"])
        self.assertEqual(result["gaps"], [])

        del data["release_review"]["distribution"]
        self.assertFalse(lib.commercial_readiness(data, {"R1": "pass"})["ready"])
        data["release_review"]["distribution"] = "web"
        del data["release_review"]["approval"]
        self.assertFalse(lib.commercial_readiness(data, {"R1": "pass"})["ready"])

    def test_failed_check_cannot_be_overridden_by_review(self):
        data = _project([{"id": "R1", "quality_dimension": "security"}])
        data["release_review"] = {"areas": {"security": {"decision": "pass", "evidence": "review.md"}}}
        result = lib.commercial_readiness(data, {"R1": "fail"})
        self.assertEqual(result["dimensions"]["security"]["status"], "failing")

    def test_not_applicable_requires_reason_and_no_linked_check(self):
        data = _project([])
        data["release_review"] = {"areas": {"privacy": {
            "decision": "not_applicable", "evidence": "scope.md", "reason": "Internal-only tool",
        }}}
        result = lib.commercial_readiness(data, {})
        self.assertEqual(result["dimensions"]["privacy"]["status"], "not_applicable")
        del data["release_review"]["areas"]["privacy"]["reason"]
        result = lib.commercial_readiness(data, {})
        self.assertEqual(result["dimensions"]["privacy"]["status"], "pending_review")
        data["release_review"]["areas"]["commercial"] = {
            "decision": "not_applicable", "evidence": "scope.md", "reason": "No sales yet",
        }
        result = lib.commercial_readiness(data, {})
        self.assertEqual(result["dimensions"]["commercial"]["status"], "pending_review")

    def test_a_failing_tagged_requirement_marks_that_dimension_failing_not_missing(self):
        requirements = [{"id": "R1", "quality_dimension": "security"}]
        result = lib.commercial_readiness(_project(requirements), {"R1": "fail"})
        self.assertFalse(result["ready"])
        self.assertEqual(result["dimensions"]["security"]["status"], "failing")
        self.assertIn("security", result["gaps"])

    def test_unrecognized_dimension_value_is_ignored(self):
        requirements = [{"id": "R1", "quality_dimension": "not-a-real-dimension"}]
        result = lib.commercial_readiness(_project(requirements), {"R1": "pass"})
        # Falls back to "missing" for every real dimension -- the bogus tag doesn't
        # silently count toward any of them.
        self.assertFalse(result["ready"])
        for info in result["dimensions"].values():
            self.assertEqual(info["requirement_ids"], [])

    def test_multiple_requirements_can_cover_the_same_dimension(self):
        requirements = [
            {"id": "R1", "quality_dimension": "security"},
            {"id": "R2", "quality_dimension": "security"},
        ]
        result = lib.commercial_readiness(_project(requirements), {"R1": "pass", "R2": "pass"})
        self.assertEqual(result["dimensions"]["security"]["requirement_ids"], ["R1", "R2"])
        self.assertEqual(result["dimensions"]["security"]["status"], "pending_review")


if __name__ == "__main__":
    unittest.main()
