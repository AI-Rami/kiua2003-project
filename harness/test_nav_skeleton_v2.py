"""Model-free checks for revised NAV extraction format."""

import json
from pathlib import Path
import tempfile
import unittest

import nav_skeleton as skeleton


SOURCE = "Preferred qualifications:\n\n- Python or R\n\n- SQL\n\nInterest in Rust."


def item(skills, relationship, classification, mention_type, skill_quote,
         context=None):
    return {"skills": skills, "relationship": relationship,
            "classification": classification, "mention_type": mention_type,
            "skill_evidence": skill_quote, "classification_context": context}


def response(items):
    return {"status": "completed", "incomplete_details": None,
            "id": "resp_synthetic", "model": skeleton.MODEL,
            "output": [{"content": [{"type": "output_text",
                                      "text": json.dumps({"items": items})}]}],
            "usage": {"input_tokens": 10, "output_tokens": 20,
                      "total_tokens": 30}}


class ExtractionV2Tests(unittest.TestCase):
    def test_schema_and_payload_identify_v2(self):
        payload = skeleton.request_payload(SOURCE, cleaned_capture=True)
        self.assertEqual(payload["input"], SOURCE)
        self.assertEqual(payload["text"]["format"]["name"], "skill_extraction_v2")
        self.assertTrue(payload["text"]["format"]["strict"])
        props = skeleton.SCHEMA["properties"]["items"]["items"]["properties"]
        self.assertEqual(set(props), {"skills", "relationship", "classification",
                                      "mention_type", "skill_evidence",
                                      "classification_context"})
        self.assertEqual(props["classification_context"]["type"], ["string", "null"])

    def test_separate_exact_quotes_or_group_and_report(self):
        items = [item(["Python", "R"], "any_of", "preferred",
                      "candidate_qualification", "- Python or R",
                      "Preferred qualifications:"),
                 item(["Rust"], "single", "unclear", "interest_only",
                      "Interest in Rust.")]
        checked, output = skeleton.validate(response(items), SOURCE)
        self.assertTrue(checked["passed"], checked["errors"])
        self.assertEqual(checked["quotation_matches"][0],
                         {"item": 1, "skill_evidence": "exact",
                          "classification_context": "exact"})
        self.assertEqual(checked["quotation_matches"][1]["classification_context"],
                         "not_provided")
        self.assertEqual(output["items"], items)
        prepared = {"uuid": "00000000-0000-0000-0000-000000000001",
                    "title": "Synthetic advertisement", "source_url": "https://example.org/ad",
                    "prepared": SOURCE}
        with tempfile.TemporaryDirectory(dir=skeleton.ROOT / "out") as temp:
            run_dir = Path(temp)
            result = skeleton.validate_and_report(response(items), prepared,
                                                  run_dir, "synthetic", "2026-11-01T00:00:00Z", 0.1)
            self.assertEqual(result["format_version"], 2)
            report = (run_dir / "report.md").read_text(encoding="utf-8")
            self.assertIn("Mention type", report)
            self.assertIn("skill: exact; context: exact", report)
            self.assertEqual(json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))["format_version"], 2)

    def test_noncontiguous_or_altered_quotes_fail(self):
        stitched = item(["SQL"], "single", "preferred", "candidate_qualification",
                        "Preferred qualifications:\n\n- SQL")
        checked, _ = skeleton.validate(response([stitched]), SOURCE)
        self.assertFalse(checked["passed"])
        self.assertIn("skill quotation is not an exact continuous passage",
                      checked["errors"][0])
        changed_context = item(["SQL"], "single", "preferred",
                               "candidate_qualification", "- SQL", "Preferred qualification:")
        checked, _ = skeleton.validate(response([changed_context]), SOURCE)
        self.assertFalse(checked["passed"])
        self.assertTrue(any("context quotation" in error for error in checked["errors"]))
        whitespace_change = item(["Python"], "single", "preferred",
                                 "candidate_qualification", "- Python  or R")
        checked, _ = skeleton.validate(response([whitespace_change]), SOURCE)
        self.assertFalse(checked["passed"])

    def test_invalid_mention_type_classification_or_and_empty_quote_fail(self):
        cases = [item(["Rust"], "single", "required", "interest_only", "Interest in Rust."),
                 item(["Python"], "any_of", "preferred", "candidate_qualification", "- Python or R"),
                 item(["SQL"], "single", "preferred", "candidate_qualification", " "),
                 item(["SQL"], "single", "preferred", "candidate_qualification", "- SQL", " ")]
        for case in cases:
            with self.subTest(case=case):
                checked, _ = skeleton.validate(response([case]), SOURCE)
                self.assertFalse(checked["passed"])


if __name__ == "__main__":
    unittest.main()
