"""Protect the feature, UI, and workflow product-acceptance gate."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import _checklist_lib as lib  # noqa: E402
import generate_checklist_dashboard as dashboard  # noqa: E402


def acceptance_case(case_id: str) -> dict:
    """Return one fully evidenced acceptance case."""
    return {
        "id": case_id,
        "title": "Complete a user task",
        "role": "operator",
        "preconditions": "A clean local test account exists",
        "steps": ["Open the page", "Submit the form", "Review the saved result"],
        "expected_result": "The saved result is visible and reusable",
        "actual_result": "The result was saved and reopened",
        "evidence": "evidence/acceptance.txt",
        "reviewer": "QA reviewer",
        "reviewed_at": "2026-10-09",
        "status": "pass",
    }


class ProductAcceptanceTests(unittest.TestCase):
    def test_requirements_create_visible_not_run_review_work(self):
        data = {
            "project": "Example",
            "requirements": [{"id": "REQ-1", "description": "보고서를 생성하고 다시 연다"}],
        }

        result = lib.product_acceptance(data)

        self.assertEqual(result["counts"]["not_run"], 3)
        self.assertEqual(result["missing_kinds"], [])
        self.assertEqual(result["kinds"]["feature"][0]["title"], "보고서를 생성하고 다시 연다")
        self.assertIn("핵심 업무 전체 흐름", result["kinds"]["workflow"][0]["title"])
        self.assertFalse(result["ready"])

    def test_mobile_dashboard_has_overflow_guards(self):
        style = (Path(__file__).resolve().parent.parent / "scripts" / "_style.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("@media (max-width: 520px)", style)
        self.assertIn("repeat(2, minmax(0, 1fr))", style)
        self.assertIn("overflow-wrap: anywhere", style)

    def test_all_three_review_kinds_need_evidenced_passes(self):
        data = {"acceptance_reviews": {
            kind: [acceptance_case(kind)] for kind in lib.ACCEPTANCE_KINDS
        }}
        result = lib.product_acceptance(data)
        self.assertTrue(result["ready"])
        self.assertEqual(result["counts"]["pass"], 3)

    def test_pass_without_actual_evidence_is_invalid(self):
        item = acceptance_case("feature-1")
        item.pop("evidence")
        result = lib.product_acceptance({"acceptance_reviews": {"feature": [item]}})
        self.assertFalse(result["ready"])
        self.assertEqual(result["counts"]["invalid"], 1)
        self.assertIn("evidence", result["invalid"][0]["missing"])

    def test_missing_review_kind_keeps_acceptance_on_hold(self):
        data = {"acceptance_reviews": {
            "feature": [acceptance_case("feature")],
            "ui": [acceptance_case("ui")],
        }}
        result = lib.product_acceptance(data)
        self.assertFalse(result["ready"])
        self.assertEqual(result["missing_kinds"], ["workflow"])

    def test_dashboard_exposes_steps_results_and_hold(self):
        item = acceptance_case("workflow-1")
        item["status"] = "not_run"
        item.pop("actual_result")
        html = dashboard.render_acceptance(lib.product_acceptance(
            {"acceptance_reviews": {"workflow": [item]}}
        ))
        self.assertIn("제품 인수검수 HOLD", html)
        self.assertIn("업무 흐름 검수", html)
        self.assertIn("Open the page", html)
        self.assertIn("NOT RUN", html)


if __name__ == "__main__":
    unittest.main()
