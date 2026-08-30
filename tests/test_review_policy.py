from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "plugins" / "axiom" / "skills" / "axiom" / "references" / "review.md"
TRACE_EVALS = ROOT / "docs" / "TRACE_EVALS.md"


class ReviewPolicyTests(unittest.TestCase):
    def test_rereview_allows_newly_evidenced_concrete_defects(self) -> None:
        review = REVIEW.read_text(encoding="utf-8").lower()
        trace_evals = TRACE_EVALS.read_text(encoding="utf-8").lower()

        self.assertIn("finding freeze constrains re-litigation", review)
        self.assertIn("including one missed by the initial review", review)
        self.assertIn("new independent current evidence demonstrates a concrete material", review)
        self.assertIn("candidate-created machinery does not create follow-on obligations", review)
        self.assertNotIn(
            "admissible only when the accepted fix directly introduced/revealed",
            review,
        )

        self.assertIn("finding freeze must not hide a concrete material", trace_evals)
        self.assertIn(
            "concrete evidenced defect versus speculative follow-on hardening",
            trace_evals,
        )


if __name__ == "__main__":
    unittest.main()
